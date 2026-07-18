"""
1688 商品详情页爬虫服务

设计目标：
- 优先使用 Playwright 渲染（最稳，1688 反爬可破），未安装时回退到 requests。
- requests 模式使用 m.1688.com 移动端页面 + 完整浏览器头 + 随机延时，作为轻量 fallback。
- 解析提取：商品大标题、型号规格参数、详情页图文内的文字介绍、产品优势描述。
- 对链接失效 / 超时 / 反爬验证 / 解析失败等情况抛出友好的 ScrapeError。

依赖：
- requests（项目已有）
- 可选：playwright（pip install playwright && playwright install chromium）

注意（坦诚的工程限制）：
- 1688 详情页大量图文内容以「图片」形式承载，图片内的文字无法在不借助 OCR 服务的情况下提取。
- 现代 1688 详情描述常懒加载在 iframe / 异步接口中，可见文字提取为「尽力而为」。
- 1688 PC 端（detail.1688.com）对 requests 非常敏感， punish 页概率极高；移动端相对宽松，但仍可能被风控。
- 高频请求会被 1688 限流，请勿在短时间去重复抓取同一链接。
"""

import re
import time
import random
from urllib.parse import urlparse, parse_qsl, urlencode

from utils.logger import log_error

try:
    import requests
except ImportError:  # pragma: no cover - 依赖缺失时给出明确错误
    requests = None

# 可选 Playwright：能安装就优先用，稳过 1688 反爬
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class ScrapeError(Exception):
    """抓取过程的可预期错误，消息可直接展示给用户。"""
    pass


# ---------------------------------------------------------------------------
# HTML 解析：基于标准库 html.parser，提取标题 / 规格表 / 可见文本
# ---------------------------------------------------------------------------
class _PageParser:
    def __init__(self):
        self.title = ''
        self.og_title = ''
        self.og_description = ''
        self.meta_description = ''
        self.h1 = []
        self.tables = []          # list[list[list[str]]] 每张表 -> 行 -> 单元格
        self._text = []           # 可见文字片段（按标签切分）
        self._skip_depth = 0      # script/style/noscript/svg/iframe 嵌套深度
        self._in_title = False
        self._in_h1 = False
        self._table = None
        self._row = None
        self._cell = None

    def feed(self, html):
        from html.parser import HTMLParser
        parser = HTMLParser(convert_charrefs=True)
        # 把方法绑定到 parser 实例上（避免继承复杂度）
        parser.title = ''
        parser.og_title = ''
        parser.og_description = ''
        parser.meta_description = ''
        parser.h1 = []
        parser.tables = []
        parser._text = []
        parser._skip_depth = 0
        parser._in_title = False
        parser._in_h1 = False
        parser._table = None
        parser._row = None
        parser._cell = None

        def handle_starttag(tag, attrs):
            a = dict(attrs)
            if tag in ('script', 'style', 'noscript', 'svg', 'iframe'):
                parser._skip_depth += 1
            if tag == 'title':
                parser._in_title = True
            elif tag == 'h1':
                parser._in_h1 = True
            elif tag == 'table':
                parser._table = []
            elif tag == 'tr' and parser._table is not None:
                parser._row = []
            elif tag in ('td', 'th') and parser._row is not None:
                parser._cell = []
            if tag == 'meta':
                prop = (a.get('property') or a.get('name') or '')
                content = a.get('content', '') or ''
                if prop == 'og:title':
                    parser.og_title = content
                elif prop == 'og:description':
                    parser.og_description = content
                elif prop.lower() == 'description':
                    parser.meta_description = content
            if tag == 'img':
                alt = (a.get('alt') or '').strip()
                if alt and len(alt) >= 2 and len(alt) <= 100:
                    parser._text.append(alt)

        def handle_endtag(tag):
            if tag in ('script', 'style', 'noscript', 'svg', 'iframe'):
                parser._skip_depth = max(0, parser._skip_depth - 1)
            if tag == 'title':
                parser._in_title = False
            elif tag == 'h1':
                parser._in_h1 = False
            elif tag == 'table' and parser._table is not None:
                if parser._table:
                    parser.tables.append(parser._table)
                parser._table = None
            elif tag == 'tr' and parser._row is not None:
                if parser._row:
                    parser._table.append(parser._row)
                parser._row = None
            elif tag in ('td', 'th') and parser._cell is not None:
                parser._row.append(' '.join(parser._cell).strip())
                parser._cell = None

        def handle_data(data):
            if parser._skip_depth > 0:
                return
            text = data.strip()
            if not text:
                return
            if parser._in_title:
                parser.title += text
            if parser._in_h1:
                parser.h1.append(text)
            if parser._cell is not None:
                parser._cell.append(text)
            else:
                parser._text.append(text)

        parser.handle_starttag = handle_starttag
        parser.handle_endtag = handle_endtag
        parser.handle_data = handle_data
        parser.feed(html)

        # 回写结果
        self.title = parser.title
        self.og_title = parser.og_title
        self.og_description = parser.og_description
        self.meta_description = parser.meta_description
        self.h1 = parser.h1
        self.tables = parser.tables
        self._text = parser._text


# ---------------------------------------------------------------------------
# 反爬 / URL 处理相关工具
# ---------------------------------------------------------------------------
_MOBILE_UAS = [
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
]

_PC_UAS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15',
]


def _is_1688_url(url):
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return False
    return '1688.com' in host


def _to_mobile_url(url):
    """把 1688 链接清洗为移动端详情页，去掉非必要追踪参数。"""
    try:
        parsed = urlparse(url)
        # 保留 offerId / id 等核心参数
        keep = {'offerId', 'offer_id', 'id', 'item_id', 'object_id'}
        qsl = [(k, v) for k, v in parse_qsl(parsed.query) if k in keep]
        clean_query = urlencode(qsl)

        # 将 detail.1688.com 或 其他 1688 域名替换为 m.1688.com
        path = parsed.path
        if path.startswith('/offer/'):
            path = '/offer/' + path.split('/')[-1].split('.')[0] + '.html'
        elif path.startswith('/m/offer/'):
            path = '/offer/' + path.split('/')[-1].split('.')[0] + '.html'

        mobile = parsed._replace(
            netloc='m.1688.com',
            path=path,
            query=clean_query
        )
        return mobile.geturl()
    except Exception:
        return url


def _looks_like_blocked(html, status_code=None):
    """粗略判断是否命中反爬验证页或返回异常。"""
    if not html or len(html) < 5000:
        # 页面极短，大概率是验证页或 204 等
        return True
    markers = ['验证码', '人机验证', '滑动验证', '请完成安全验证', 'captcha',
               'verify you are human', 'robot check', '访问过于频繁', 'punish',
               '_____tmd_____', 'x5secdata']
    low = html.lower()
    return any(m.lower() in low for m in markers)


def _clean_visible_text(text_parts):
    """拼接并清理可见文字，去除空行与重复。"""
    text = '\n'.join(p for p in text_parts if p and p.strip())
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _extract_specs(tables):
    """从表格中提取 规格参数（键值对）。"""
    specs = []
    seen = set()
    for table in tables:
        for row in table:
            cells = [c for c in row if c]
            if len(cells) >= 2:
                key = cells[0].strip()
                value = ' '.join(cells[1:]).strip()
                if not key or not value:
                    continue
                if key in seen:
                    continue
                # 过滤纯数字行 / 无意义行
                if re.fullmatch(r'[\d\s./%-]+', key):
                    continue
                seen.add(key)
                specs.append({'key': key, 'value': value})
    return specs[:40]


def _extract_advantages(full_text):
    """尽力从可见文字中扫描产品优势 / 特点 / 卖点描述。"""
    keywords = ['优势', '特点', '卖点', '功能', '特色', '亮点', '好处',
                '采用', '支持', '具备', '专为', '适用']
    segments = re.split(r'[。！？\n;；]', full_text)
    advantages = []
    for seg in segments:
        seg = seg.strip()
        if 4 <= len(seg) <= 50 and any(k in seg for k in keywords):
            if seg not in advantages:
                advantages.append(seg)
        if len(advantages) >= 12:
            break
    return advantages


def _extract_json_offer(html):
    """
    尝试从 1688 页面内嵌 JSON 中解析商品标题、描述、规格、卖点。
    1688 移动端常把商品数据放在 <script> 标签或全局变量里。
    返回 dict 或 None；命中字段包括 title, description, specs, advantages。
    """
    import json
    candidates = []
    # 常见内嵌数据变量名
    for marker in ['window.__INITIAL_STATE__', 'window._GLOBAL_DATA', 'window._INITDATA',
                   'window.g_config', 'window._data']:
        idx = html.find(marker)
        if idx == -1:
            continue
        start = html.find('=', idx) + 1
        end = html.find(';</script>', start)
        if end == -1:
            end = html.find(';\n', start)
        if end == -1:
            continue
        try:
            data = json.loads(html[start:end].strip())
            candidates.append(data)
        except json.JSONDecodeError:
            continue

    # 尝试从任何 JSON 里捞取字段
    result = {'title': '', 'description': '', 'specs': [], 'advantages': []}
    for data in candidates:
        try:
            # 尝试找到标题
            for path in [
                ['offerBaseInfo', 'subject'],
                ['subject'],
                ['offerBaseInfo', 'title'],
                ['title'],
                ['data', 'offerBaseInfo', 'subject'],
            ]:
                cur = data
                for p in path:
                    if isinstance(cur, dict):
                        cur = cur.get(p)
                    else:
                        cur = None
                        break
                if isinstance(cur, str) and cur:
                    result['title'] = result['title'] or cur
                    break

            # 尝试找到描述
            for path in [
                ['offerDescInfo', 'description'],
                ['description'],
                ['offerDesc'],
                ['detail'],
            ]:
                cur = data
                for p in path:
                    if isinstance(cur, dict):
                        cur = cur.get(p)
                    else:
                        cur = None
                        break
                if isinstance(cur, str) and cur:
                    result['description'] = result['description'] or cur
                    break

            # 尝试找到规格列表
            for path in [
                ['skuProps'],
                ['offerBaseInfo', 'skuProps'],
                ['productProp'],
            ]:
                cur = data
                for p in path:
                    if isinstance(cur, dict):
                        cur = cur.get(p)
                    else:
                        cur = None
                        break
                if isinstance(cur, list):
                    for prop in cur:
                        if isinstance(prop, dict):
                            name = prop.get('name') or prop.get('prop') or prop.get('key') or ''
                            vals = prop.get('value') or prop.get('values') or []
                            if isinstance(vals, list):
                                val = ' / '.join(str(v) for v in vals if v)
                            else:
                                val = str(vals)
                            if name and val:
                                result['specs'].append({'key': name, 'value': val})
                            if len(result['specs']) >= 30:
                                break

            # 尝试找到卖点 / 优势列表
            for path in [
                ['saleInfo', 'sellPoints'],
                ['offerBaseInfo', 'sellPoints'],
                ['sellPoints'],
            ]:
                cur = data
                for p in path:
                    if isinstance(cur, dict):
                        cur = cur.get(p)
                    else:
                        cur = None
                        break
                if isinstance(cur, list):
                    for sp in cur:
                        if isinstance(sp, str) and sp.strip():
                            result['advantages'].append(sp.strip())
                        elif isinstance(sp, dict):
                            txt = sp.get('text') or sp.get('name') or ''
                            if txt:
                                result['advantages'].append(txt.strip())
        except Exception:
            continue

    return result if any(result.values()) else None


def _extract_img_alts(text_parts):
    """从可见文字或 HTML 片段中提取图片 alt 属性，作为卖点/描述补充。"""
    # text_parts 中可能包含 img 标签的 alt 文本，已经由 HTMLParser 解析到 _text
    alts = []
    for p in text_parts:
        if len(p) >= 4 and len(p) <= 80 and p not in alts:
            alts.append(p)
    return alts[:20]


# ---------------------------------------------------------------------------
# 请求抓取（fallback）
# ---------------------------------------------------------------------------
def _build_mobile_headers():
    ua = random.choice(_MOBILE_UAS)
    return {
        'User-Agent': ua,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer': 'https://m.1688.com/',
        'Upgrade-Insecure-Requests': '1',
        'sec-ch-ua': '"Chromium";v="112", "Google Chrome";v="112"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
    }


def _scrape_requests(url, timeout=20):
    """使用 requests + m.1688.com 移动端抓取。"""
    if requests is None:
        raise ScrapeError('服务端缺少 requests 依赖，无法执行抓取')

    mobile_url = _to_mobile_url(url)
    headers = _build_mobile_headers()
    time.sleep(random.uniform(0.4, 1.2))  # 反爬：随机延时间隔（已压缩提速）

    try:
        resp = requests.get(mobile_url, headers=headers, timeout=timeout, allow_redirects=True)
    except requests.exceptions.Timeout:
        raise ScrapeError('抓取超时（1688 响应过慢），请稍后重试')
    except requests.exceptions.ConnectionError:
        raise ScrapeError('网络连接失败，无法访问 1688，请检查网络后重试')
    except Exception as e:
        log_error('scraper', e)
        raise ScrapeError(f'抓取时发生错误：{str(e)[:80]}')

    if resp.status_code == 404:
        raise ScrapeError('商品页面不存在（404），链接可能已失效')
    if resp.status_code in (403, 429):
        raise ScrapeError('1688 拒绝访问（403/429），触发了频率限制，请稍后重试')
    if resp.status_code != 200:
        raise ScrapeError(f'1688 返回异常状态码 {resp.status_code}，抓取失败')

    html = resp.text or ''
    if _looks_like_blocked(html, resp.status_code):
        raise ScrapeError(
            '1688 触发了反爬验证（验证码/滑块），建议：\n'
            '1. 在浏览器中打开该链接并登录 1688；\n'
            '2. 安装 Playwright 可稳定绕过反爬（pip install playwright && playwright install chromium）；\n'
            '3. 等待几分钟后重试。'
        )

    return html, mobile_url


# ---------------------------------------------------------------------------
# Playwright 抓取（优先，最稳）
# ---------------------------------------------------------------------------
def _scrape_playwright(url, timeout=30):
    """使用 Playwright 浏览器渲染抓取，1688 反爬通过率最高。"""
    if not PLAYWRIGHT_AVAILABLE:
        raise ScrapeError('Playwright 未安装，跳过浏览器渲染模式')

    mobile_url = _to_mobile_url(url)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=random.choice(_MOBILE_UAS),
                viewport={'width': 390, 'height': 844},
                locale='zh-CN',
                timezone_id='Asia/Shanghai',
            )
            page = context.new_page()
            page.set_extra_http_headers({
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Referer': 'https://m.1688.com/',
            })
            page.goto(mobile_url, wait_until='domcontentloaded', timeout=timeout * 1000)
            time.sleep(random.uniform(0.6, 1.2))  # 等详情懒加载（已压缩提速）
            html = page.content()
            browser.close()
            return html, mobile_url
    except PlaywrightTimeout:
        raise ScrapeError('浏览器抓取超时，请稍后重试')
    except Exception as e:
        log_error('scraper', e)
        raise ScrapeError(f'浏览器抓取失败：{str(e)[:80]}')


# ---------------------------------------------------------------------------
# 解析提取
# ---------------------------------------------------------------------------
def _parse_html(html, source_url, mobile_url):
    parser = _PageParser()
    try:
        parser.feed(html)
    except Exception as e:
        log_error('scraper', e)
        raise ScrapeError('页面解析失败，可能页面结构异常')

    # 1. 基础解析
    title = (parser.og_title or parser.title or (parser.h1[0] if parser.h1 else '')).strip()
    visible_text = _clean_visible_text(parser._text)
    specs = _extract_specs(parser.tables)
    description_src = parser.og_description or parser.meta_description or visible_text
    description_text = description_src.strip()
    advantages = _extract_advantages(visible_text)

    # 2. 尝试从页面内嵌 JSON 补强数据（1688 移动端常把商品数据放在 <script> 里）
    try:
        json_offer = _extract_json_offer(html)
        if json_offer:
            title = title or json_offer.get('title', '')
            description_text = description_text or json_offer.get('description', '')
            if json_offer.get('specs'):
                specs = specs or json_offer['specs']
            if json_offer.get('advantages'):
                advantages = advantages or json_offer['advantages']
    except Exception as e:
        log_error('scraper', f'JSON extraction failed: {e}')

    # 3. 图片 alt 文本也可作为补充卖点
    img_alts = _extract_img_alts(parser._text)
    if img_alts and not advantages:
        advantages = img_alts[:8]

    if len(description_text) > 6000:
        description_text = description_text[:6000] + '…（已截断）'

    notes = []
    if not specs:
        notes.append('未能从页面表格中提取到规格参数，可能参数以图片形式展示。')
    if not advantages:
        notes.append('未扫描到明显"优势/特点"描述，AI 将在提炼阶段基于详情文本归纳卖点。')
    if parser.og_description or parser.meta_description:
        notes.append('详情描述取自页面 meta 信息，可能不含完整图文正文。')
    if not parser.og_description and not parser.meta_description:
        notes.append('详情描述来自页面可见文字，可能受懒加载影响而不完整。')

    raw_text_for_llm = _build_raw_for_llm(title, specs, description_text, advantages)

    if not title and not description_text:
        raise ScrapeError('未能从页面解析出有效内容，可能页面需要登录或结构已变动')

    return {
        'url': source_url,
        'fetch_url': mobile_url,
        'title': title,
        'specs': specs,
        'description_text': description_text,
        'advantages': advantages,
        'raw_text_for_llm': raw_text_for_llm,
        'notes': notes,
    }


# ---------------------------------------------------------------------------
# 对外主入口
# ---------------------------------------------------------------------------
def scrape_1688(url, timeout=20):
    """
    抓取并解析 1688 商品详情页。

    返回 dict:
    {
      'url', 'fetch_url', 'title', 'specs', 'description_text', 'advantages',
      'raw_text_for_llm', 'notes' (list)
    }
    失败时抛出 ScrapeError。
    """
    if not url or not isinstance(url, str):
        raise ScrapeError('请输入商品链接')
    if not _is_1688_url(url):
        raise ScrapeError('链接不属于 1688 商品详情页，请粘贴有效的 1688 链接（含 1688.com）')

    # 优先 Playwright，其次 requests
    errors = []
    if PLAYWRIGHT_AVAILABLE:
        try:
            html, mobile_url = _scrape_playwright(url, timeout=timeout + 10)
            return _parse_html(html, url, mobile_url)
        except ScrapeError as e:
            errors.append(f'Playwright: {e}')

    try:
        html, mobile_url = _scrape_requests(url, timeout=timeout)
        return _parse_html(html, url, mobile_url)
    except ScrapeError as e:
        errors.append(f'requests: {e}')
        raise ScrapeError('\n'.join(errors))


def _build_raw_for_llm(title, specs, description_text, advantages):
    parts = []
    if title:
        parts.append(f'【商品标题】{title}')
    if specs:
        spec_lines = '\n'.join(f'- {s["key"]}: {s["value"]}' for s in specs)
        parts.append(f'【规格参数】\n{spec_lines}')
    if advantages:
        adv_lines = '\n'.join(f'- {a}' for a in advantages)
        parts.append(f'【产品优势(抓取)】\n{adv_lines}')
    if description_text:
        parts.append(f'【详情描述】\n{description_text}')
    return '\n\n'.join(parts)[:6000]
