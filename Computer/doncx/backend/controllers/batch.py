from flask import Blueprint, request, jsonify
from utils.db import add_copywriter_record, DEFAULT_MERCHANT
from services.llm_service import LLMService
from utils.validator import validate_request
import json
import concurrent.futures

bp = Blueprint('batch', __name__)
llm = LLMService()

@bp.route('/generate', methods=['POST'])
def batch_generate():
    """批量生成文案：一次传入多条产品描述，并行生成"""
    data = request.get_json() or {}
    items = data.get('items', [])
    platform = data.get('platform', 'amazon')
    target_language = data.get('target_language', 'en')

    if not items or not isinstance(items, list):
        return jsonify({'success': False, 'message': '请提供 items 数组'}), 400
    if len(items) > 20:
        return jsonify({'success': False, 'message': '单次最多20条'}), 400

    results = [None] * len(items)

    def generate_one(idx, item):
        desc = item.get('desc', '') or item.get('product_desc', '') or str(item)
        try:
            result = llm.generate_copywriter(
                product_desc=desc,
                platform=platform,
                target_language=target_language
            )
            add_copywriter_record(
                DEFAULT_MERCHANT, 'batch', platform, target_language,
                desc, json.dumps(result, ensure_ascii=False)
            )
            results[idx] = {'index': idx, 'desc': desc[:60], 'success': True, 'data': result}
        except Exception as e:
            results[idx] = {'index': idx, 'desc': desc[:60], 'success': False, 'error': str(e)}

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(generate_one, i, item) for i, item in enumerate(items)]
        concurrent.futures.wait(futures)

    return jsonify({'success': True, 'data': results})


@bp.route('/compliance-scan', methods=['POST'])
def batch_compliance():
    """批量合规审查"""
    data = request.get_json() or {}
    items = data.get('items', [])
    check_extreme = data.get('check_extreme_words', True)
    check_copyright = data.get('check_copyright', True)
    check_forbidden = data.get('check_forbidden_words', True)

    if not items or not isinstance(items, list):
        return jsonify({'success': False, 'message': '请提供 items 数组'}), 400
    if len(items) > 20:
        return jsonify({'success': False, 'message': '单次最多20条'}), 400

    results = [None] * len(items)

    def scan_one(idx, item):
        text = item.get('text', '') or item.get('content', '') or str(item)
        try:
            result = llm.scan_compliance(
                content=text,
                check_extreme_words=check_extreme,
                check_copyright=check_copyright,
                check_forbidden_words=check_forbidden
            )
            results[idx] = {'index': idx, 'text': text[:60], 'success': True, 'data': result}
        except Exception as e:
            results[idx] = {'index': idx, 'text': text[:60], 'success': False, 'error': str(e)}

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(scan_one, i, item) for i, item in enumerate(items)]
        concurrent.futures.wait(futures)

    return jsonify({'success': True, 'data': results})
