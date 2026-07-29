import json

from flask import Blueprint, request, jsonify
from services.llm_service import LLMService
from utils.validator import ComplianceScanSchema, ImageAnalyzeSchema, validate_request
from utils.logger import log_error
from utils.db import (
    list_compliance_records, add_compliance_record,
    delete_compliance_record, clear_compliance_records, DEFAULT_MERCHANT
)
from utils.image_analyzer import analyze_images, format_image_text_for_scan

bp = Blueprint('compliance', __name__)
llm_service = LLMService()


def _merchant():
    body = request.get_json(silent=True) or {}
    return body.get('merchant_id') or request.args.get('merchant_id') or DEFAULT_MERCHANT


@bp.route('/scan', methods=['POST'])
def scan():
    data = request.get_json()
    validation = validate_request(ComplianceScanSchema, data)

    if not validation['valid']:
        return jsonify({'success': False, 'errors': validation['errors']}), 400

    content = data.get('content', '')
    images = data.get('images', []) or []

    if not content.strip() and not images:
        return jsonify({'success': False, 'message': '请输入商品文案或上传图片'}), 400

    check_extreme_words = data.get('check_extreme_words', True)
    check_copyright = data.get('check_copyright', True)
    check_forbidden_words = data.get('check_forbidden_words', True)

    # 1) 分析图片：提取文字 + 描述
    image_analysis = analyze_images(images, client=llm_service.client)
    image_texts = format_image_text_for_scan(image_analysis)

    # 2) 图片内容追加到待审查文案
    combined_content = content
    if image_texts:
        combined_content = f"{content}\n\n{image_texts}".strip()

    # 3) 大模型合规检测
    result = llm_service.scan_compliance(
        combined_content,
        check_extreme_words,
        check_copyright,
        check_forbidden_words,
        image_texts=image_texts
    )

    if result and 'error' in result:
        return jsonify({'success': False, 'message': result['error']}), 400

    # 4) 保存历史记录（含图片分析结果）
    options = {
        'check_extreme_words': check_extreme_words,
        'check_copyright': check_copyright,
        'check_forbidden_words': check_forbidden_words
    }
    merchant_id = _merchant()
    try:
        rec_id = add_compliance_record(
            merchant_id,
            content,
            json.dumps(options, ensure_ascii=False),
            json.dumps(result, ensure_ascii=False),
            json.dumps(image_analysis, ensure_ascii=False)
        )
    except Exception as e:
        log_error('compliance.scan.add_record', e)
        rec_id = None

    if result:
        return jsonify({
            'success': True,
            'data': result,
            'record_id': rec_id,
            'image_analysis': image_analysis
        })
    return jsonify({'success': False, 'message': 'Failed to scan compliance'}), 500


@bp.route('/analyze-image', methods=['POST'])
def analyze_image():
    """单张图片分析：OCR + 图像描述，返回结构化结果，不保存历史。"""
    data = request.get_json()
    validation = validate_request(ImageAnalyzeSchema, data)

    if not validation['valid']:
        return jsonify({'success': False, 'errors': validation['errors']}), 400

    name = data.get('name', 'image.png')
    base64 = data.get('base64', '')
    result = analyze_images([{'name': name, 'base64': base64}], client=llm_service.client)

    return jsonify({
        'success': True,
        'data': result[0] if result else None
    })


@bp.route('/history', methods=['GET'])
def history_list():
    try:
        records = list_compliance_records(_merchant())
        for r in records:
            if r.get('result_json'):
                try:
                    r['result'] = json.loads(r['result_json'])
                except Exception:
                    r['result'] = None
            r.pop('result_json', None)
            if r.get('options_json'):
                try:
                    r['options'] = json.loads(r['options_json'])
                except Exception:
                    r['options'] = None
            r.pop('options_json', None)
            if r.get('images_json'):
                try:
                    r['images'] = json.loads(r['images_json'])
                except Exception:
                    r['images'] = []
            r.pop('images_json', None)
        return jsonify({'success': True, 'data': records})
    except Exception as e:
        log_error('compliance.history_list', e)
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/history', methods=['POST'])
def history_add():
    data = request.get_json() or {}
    try:
        options = {
            'check_extreme_words': data.get('check_extreme_words', True),
            'check_copyright': data.get('check_copyright', True),
            'check_forbidden_words': data.get('check_forbidden_words', True)
        }
        rec_id = add_compliance_record(
            _merchant(),
            data.get('content', ''),
            json.dumps(options, ensure_ascii=False),
            json.dumps(data.get('result', {}), ensure_ascii=False),
            json.dumps(data.get('images', []), ensure_ascii=False)
        )
        return jsonify({'success': True, 'data': {'id': rec_id}})
    except Exception as e:
        log_error('compliance.history_add', e)
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/history/<int:rec_id>', methods=['DELETE'])
def history_delete(rec_id):
    try:
        delete_compliance_record(_merchant(), rec_id)
        return jsonify({'success': True, 'data': {'id': rec_id}})
    except Exception as e:
        log_error('compliance.history_delete', e)
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/history', methods=['DELETE'])
def history_clear():
    try:
        clear_compliance_records(_merchant())
        return jsonify({'success': True, 'data': None})
    except Exception as e:
        log_error('compliance.history_clear', e)
        return jsonify({'success': False, 'message': str(e)}), 500
