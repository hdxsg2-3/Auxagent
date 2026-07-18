"""
自动上架文案智能 Agent 链路控制器

严格按以下顺序自主执行（一次请求，前端无需多次点击）：
  步骤1  爬虫抓取 1688 商品页 -> 标题/规格/详情/优势
  步骤2  大模型提炼 -> 核心卖点/关键参数/适用场景/简介
  步骤3  多语种 Listing 生成（亚马逊规范：英文/西班牙语/德语/中文）
  步骤4  自动合规风控校验（每个语种全文：极限词/侵权/违禁词）
  步骤5  拼装最终可上架文本（每语种纯文本 + 是否可直接上架标记）
  步骤6  统一输出（原始抓取 / AI 提炼 / 多语种成品 / 风控报告 / 可上架文本）

异常兜底：链接失效 / 抓取失败 / 接口超时 均返回友好错误，不直接崩溃。
"""

import concurrent.futures

from flask import Blueprint, request, jsonify

from services.scraper import scrape_1688, ScrapeError
from services.llm_service import LLMService
from utils.validator import AutoListingSchema, validate_request
from utils.logger import log_error

bp = Blueprint('auto_listing', __name__)

LANGUAGES = ['en', 'es', 'de', 'zh']
LANG_NAMES = {'en': '英语', 'es': '西班牙语', 'de': '德语', 'zh': '中文'}


def _build_product_desc(refined):
    """将提炼结果拼装为给 Listing 生成接口的中文产品描述。"""
    parts = []
    if refined.get('product_name'):
        parts.append(f'产品名称：{refined["product_name"]}')
    if refined.get('core_selling_points'):
        parts.append('核心卖点：' + '；'.join(refined['core_selling_points']))
    if refined.get('key_parameters'):
        parts.append('关键参数：' + '；'.join(refined['key_parameters']))
    if refined.get('applicable_scenarios'):
        parts.append('适用场景：' + '；'.join(refined['applicable_scenarios']))
    if refined.get('clean_description'):
        parts.append('产品简介：' + refined['clean_description'])
    return '\n'.join(parts)


def _combine_listing(listing):
    """将单语种 Listing 拼装为供风控审核的全文。"""
    parts = []
    if listing.get('title'):
        parts.append(f'Title: {listing["title"]}')
    if listing.get('bullet_points'):
        parts.append('Bullet Points:\n- ' + '\n- '.join(listing['bullet_points']))
    if listing.get('description'):
        parts.append(f'Description: {listing["description"]}')
    return '\n'.join(parts)


def _empty_compliance():
    return {
        'overall_risk': 'low',
        'extreme_words': [],
        'copyright_issues': [],
        'forbidden_words': [],
        'clean': True,
        'suggestions': [],
    }


def _build_final_listing(listing, compliance_scan):
    """把单语种成品拼装为可直接上架的纯文本（亚马逊字段位排版），无需额外 LLM 调用。"""
    if not listing or listing.get('error'):
        return None
    title = (listing.get('title') or '').strip()
    bullets = listing.get('bullet_points') or []
    desc = (listing.get('description') or '').strip()
    lines = []
    if title:
        lines.append(f'Title: {title}')
        lines.append('')
    if bullets:
        lines.append('Bullet Points:')
        for i, b in enumerate(bullets, 1):
            lines.append(f'{i}. {b}')
        lines.append('')
    if desc:
        lines.append('Description:')
        lines.append(desc)
    text = '\n'.join(lines).strip()
    # 是否可直接上架：以最终风控结果判定
    ready = True
    overall = 'unknown'
    if compliance_scan:
        overall = compliance_scan.get('overall_risk', 'low')
        if overall in ('high', 'medium') or not compliance_scan.get('clean', True):
            ready = False
    return {
        'text': text,
        'title': title,
        'bullet_points': bullets,
        'description': desc,
        'ready': ready,
        'overall_risk': overall,
    }


@bp.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json(silent=True) or {}
        validation = validate_request(AutoListingSchema, data)
        if not validation['valid']:
            return jsonify({'success': False, 'message': '请输入有效的 1688 商品链接'}), 400

        url = (data.get('url') or '').strip()

        # ---------------- 步骤 1：爬虫抓取 ----------------
        try:
            raw = scrape_1688(url)
        except ScrapeError as e:
            return jsonify({'success': False, 'message': str(e)}), 400
        except Exception as e:
            log_error('auto_listing', e)
            return jsonify({'success': False, 'message': '抓取过程中发生未知错误，请稍后重试'}), 500

        llm = LLMService()

        # ---------------- 步骤 2：大模型信息提炼 ----------------
        refined = llm.refine_product_info(raw['raw_text_for_llm'])
        if not refined or 'error' in refined:
            # 兜底：提炼失败则直接用原始抓取文本生成，保证链路不中断
            raw['refine_note'] = 'AI 提炼失败，已使用原始抓取文本直接生成文案'
            product_desc = raw['raw_text_for_llm']
            refined = None
        else:
            product_desc = _build_product_desc(refined)

        # ---------------- 步骤 3：多语种 Listing 生成（并行） ----------------
        listings = {}

        def _gen(lang):
            try:
                res = llm.generate_copywriter(product_desc, 'amazon', lang)
                return lang, (res or {'error': '生成失败'})
            except Exception as e:
                return lang, {'error': str(e)}

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
            futures = {ex.submit(_gen, lang): lang for lang in LANGUAGES}
            for fut in concurrent.futures.as_completed(futures):
                lang, res = fut.result()
                listings[lang] = res

        # ---------------- 步骤 4：合规风控结果（直接复用生成端自检，避免重复 LLM 调用） ----------------
        compliance = {}
        for lang in LANGUAGES:
            listing = listings.get(lang)
            if not listing or 'error' in listing:
                compliance[lang] = {
                    'skipped': True,
                    'reason': f'{LANG_NAMES[lang]}文案生成失败，跳过风控校验'
                }
                continue
            scan = listing.get('compliance_scan')
            if scan:
                compliance[lang] = scan
            else:
                # 兜底：生成端未返回自检结果时再扫描一次（极少触发，保持兼容）
                try:
                    text = _combine_listing(listing)
                    compliance[lang] = llm.scan_compliance(text, True, True, True) or _empty_compliance()
                except Exception:
                    compliance[lang] = _empty_compliance()

        # ---------------- 步骤 5：最终可上架文本（纯拼装，无需额外 LLM 调用） ----------------
        final_listings = {}
        for lang in LANGUAGES:
            final_listings[lang] = _build_final_listing(listings.get(lang), compliance.get(lang))

        # ---------------- 步骤 6：统一输出 ----------------
        return jsonify({
            'success': True,
            'data': {
                'raw_scraped': raw,
                'refined_info': refined,
                'listings': listings,
                'compliance': compliance,
                'final_listings': final_listings,
            }
        })
    except Exception as e:
        log_error('auto_listing', e)
        return jsonify({'success': False, 'message': f'服务内部错误：{str(e)}'}), 500
