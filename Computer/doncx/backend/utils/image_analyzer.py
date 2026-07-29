"""图片分析工具：提取文字、描述图像内容。

支持三种识别策略（按优先级）：
1. 大模型视觉能力（如果配置的模型支持 image_url 多模态输入）
2. OCR 引擎 Tesseract（如果系统已安装 tesseract 二进制和 pytesseract）
3. 基于文件名 + 元数据的文本回退描述（始终可用）

设计为：始终返回结构化结果，不抛异常。
"""
import base64
import io
import json
import os
from PIL import Image
from utils.api_client import APIClient
from utils.logger import log_error

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


# 常见电商图片文件名关键字映射到描述
_FILENAME_KEYWORDS = [
    (['pack', 'package', 'box', 'bag', 'pouch', 'sachet', '包装', '袋', '盒', '包'],
     '产品包装图片，可能包含品牌 Logo、成分表、使用说明、警告语等文字'),
    (['label', 'tag', '吊牌', '标签', '洗标', 'carelabel'],
     '产品标签/吊牌图片，可能包含材质、产地、洗涤说明、警告语等文字'),
    (['cert', 'ce', 'fcc', 'rohs', 'ul', 'ccc', '认证', '证书', '检测报告'],
     '产品认证证书或合规检测报告图片，可能包含认证标志、检测结论等文字'),
    (['ad', 'banner', 'poster', 'flyer', '宣传', '海报', '广告', '推广图'],
     '商品宣传图或广告素材，可能包含营销卖点、功效宣称、价格信息'),
    (['screenshot', 'screen', 'capture', '截图', '文档', 'text', 'ocr', 'doc'],
     '文字截图或电子文档图片，主要包含可识别的文字内容'),
    (['invoice', 'receipt', 'bill', '发票', '单据', '小票', '订单'],
     '发票、单据或订单截图，可能包含商品名称、价格、购买信息等'),
    (['ingredient', 'composition', 'formula', '成分', '配料表', '材质'],
     '成分表或材质说明图片，可能包含产品配方、含量、警示信息'),
    (['warning', 'caution', 'danger', '警告', '注意', '禁用'],
     '警示标签或注意事项图片，可能包含安全警告、禁用人群等合规敏感信息'),
]


def _guess_description_from_filename(filename):
    if not filename:
        return '商品图片或营销素材，具体内容需识别确认'
    name = filename.lower()
    for keywords, desc in _FILENAME_KEYWORDS:
        if any(k in name for k in keywords):
            return desc
    return '商品图片或营销素材，可能包含产品外观、文字说明、品牌标识等内容'


def _strip_data_uri(base64_data):
    if isinstance(base64_data, str) and ',' in base64_data:
        return base64_data.split(',', 1)[1]
    return base64_data or ''


def _image_mime_from_format(img_format):
    if not img_format:
        return 'image/png'
    fmt = img_format.lower()
    if fmt in ('jpg', 'jpeg'):
        return 'image/jpeg'
    if fmt == 'png':
        return 'image/png'
    if fmt == 'gif':
        return 'image/gif'
    if fmt == 'webp':
        return 'image/webp'
    return 'image/png'


def _extract_json_dict(text, default_keys):
    """从文本中提取第一个 JSON 对象，并确保包含 default_keys。"""
    if not text:
        return None
    try:
        start = text.find('{')
        end = text.rfind('}')
        if start == -1 or end == -1 or end <= start:
            return None
        data = json.loads(text[start:end + 1])
        if isinstance(data, dict):
            return {k: str(data.get(k, '')).strip() for k in default_keys}
    except Exception:
        pass
    return None


def _call_vision_llm(client, base64_data, filename, img_format):
    """调用大模型视觉能力。如果模型不支持 vision，API 会返回错误，外层会回退。"""
    mime = _image_mime_from_format(img_format)
    data_url = f'data:{mime};base64,{base64_data}'

    messages = [{
        'role': 'user',
        'content': [
            {
                'type': 'text',
                'text': (
                    '请分析这张图片。以 JSON 格式返回：{"text": "图片中可识别的文字（没有则空字符串）", '
                    '"description": "图片内容描述（50字以内）"}。只返回 JSON，不要解释。'
                )
            },
            {'type': 'image_url', 'image_url': {'url': data_url}}
        ]
    }]

    response, error = client.call_llm(messages)
    if error or not response:
        raise RuntimeError(error or 'Empty vision response')

    parsed = _extract_json_dict(response, ['text', 'description'])
    if parsed:
        return parsed

    # 没有解析到 JSON，把整个回应当成描述
    return {'text': '', 'description': response.strip()[:200]}


def _call_text_fallback_llm(client, filename, img_format, width, height):
    """当视觉/OCR 都不可用时，用文件名和元数据让 LLM 推测图片内容。"""
    prompt = f'''用户上传了一张图片用于电商合规审查。
图片文件名：{filename}
图片格式：{img_format or '未知'}
图片尺寸：{width}×{height}

请根据文件名推测图片内容，并以 JSON 格式返回：
{{"description": "图片可能包含的内容描述（50字以内）", "likely_text": "图片中可能出现的文字（没有则空字符串）"}}

只返回 JSON，不要解释。'''

    response, error = client.call_llm([{'role': 'user', 'content': prompt}])
    if error or not response:
        return None

    parsed = _extract_json_dict(response, ['description', 'likely_text'])
    if parsed and parsed.get('description'):
        return parsed['description']
    return None


def analyze_image(base64_data, filename='image.png', client=None):
    """
    分析单张图片，返回结构化结果。

    返回：
    {
        'text': '识别出的文字（可能为空）',
        'description': '图像内容描述',
        'format': 'JPEG/PNG/...',
        'width': 宽度,
        'height': 高度,
        'size': 文件字节数
    }
    """
    if not client:
        client = APIClient()

    if not base64_data:
        return {
            'text': '',
            'description': '无法解析空图片',
            'format': '', 'width': 0, 'height': 0, 'size': 0,
            'filename': filename or 'image.png'
        }

    try:
        raw = _strip_data_uri(base64_data)
        raw_bytes = base64.b64decode(raw)
        size = len(raw_bytes)

        img = Image.open(io.BytesIO(raw_bytes))
        width, height = img.size
        img_format = (img.format or 'UNKNOWN').upper()

        extracted_text = ''
        description = ''

        # 1. 优先尝试大模型视觉
        try:
            vision_result = _call_vision_llm(client, raw, filename, img_format)
            extracted_text = vision_result.get('text', '').strip()
            description = vision_result.get('description', '').strip()
        except Exception as e:
            log_error('ImageAnalyzer', f'Vision LLM failed: {e}')

        # 2. 视觉失败时尝试 Tesseract OCR
        if not extracted_text and TESSERACT_AVAILABLE:
            try:
                img_rgb = img.convert('RGB') if img.mode in ('RGBA', 'P', 'LA', 'L') else img
                ocr_text = pytesseract.image_to_string(img_rgb, lang='chi_sim+eng').strip()
                if ocr_text:
                    extracted_text = ocr_text
                    description = '图片包含可识别文字内容'
            except Exception as e:
                log_error('ImageAnalyzer', f'Tesseract OCR failed: {e}')

        # 3. 还没有描述时，用 LLM 文本回退
        if not description:
            try:
                fallback = _call_text_fallback_llm(client, filename, img_format, width, height)
                if fallback:
                    description = fallback
            except Exception as e:
                log_error('ImageAnalyzer', f'Text fallback LLM failed: {e}')

        # 4. 最终兜底
        if not description:
            description = _guess_description_from_filename(filename)
        if not extracted_text:
            extracted_text = ''

        return {
            'text': extracted_text,
            'description': description,
            'format': img_format,
            'width': width,
            'height': height,
            'size': size,
            'filename': filename or 'image.png'
        }
    except Exception as e:
        log_error('ImageAnalyzer', f'Image analysis failed: {e}')
        return {
            'text': '',
            'description': _guess_description_from_filename(filename),
            'format': '', 'width': 0, 'height': 0, 'size': 0,
            'filename': filename or 'image.png'
        }


def analyze_images(images, client=None):
    """
    批量分析图片。

    images: [{ 'name': 'xxx.png', 'base64': 'data:image/png;base64,....' }, ...]
    返回：[{ 'name', 'text', 'description', 'format', 'width', 'height', 'size' }, ...]
    """
    if not images:
        return []
    results = []
    for item in images:
        if not isinstance(item, dict):
            continue
        name = item.get('name', 'image.png')
        b64 = item.get('base64', '')
        result = analyze_image(b64, name, client)
        result['name'] = name
        results.append(result)
    return results


def format_image_text_for_scan(image_results):
    """将图片分析结果格式化为一段可追加到审查文本中的描述。"""
    if not image_results:
        return ''
    parts = []
    for idx, r in enumerate(image_results, 1):
        lines = [f'【图片{idx}】{r.get("name", "")}']
        if r.get('description'):
            lines.append(f'图像描述：{r.get("description")}')
        if r.get('text'):
            lines.append(f'识别文字：{r.get("text")}')
        if not r.get('description') and not r.get('text'):
            lines.append(f'格式：{r.get("format", "")}，尺寸：{r.get("width", 0)}×{r.get("height", 0)}')
        parts.append('\n'.join(lines))
    return '\n\n'.join(parts)
