import json

from flask import Blueprint, request, jsonify
from services.llm_service import LLMService
from utils.validator import CopywriterGenerateSchema, CopywriterTranslateSchema, validate_request
from utils.logger import log_error
from utils.db import (
    list_copywriter_records, add_copywriter_record,
    delete_copywriter_record, clear_copywriter_records, DEFAULT_MERCHANT
)

bp = Blueprint('copywriter', __name__)

@bp.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    validation = validate_request(CopywriterGenerateSchema, data)
    
    if not validation['valid']:
        return jsonify({'success': False, 'errors': validation['errors']}), 400
    
    try:
        llm_service = LLMService()
        result = llm_service.generate_copywriter(
            data['product_desc'],
            data['platform'],
            data['target_language']
        )
        
        if result and 'error' in result:
            return jsonify({'success': False, 'message': result['error']}), 400
        
        if result:
            return jsonify({'success': True, 'data': result})
        
        return jsonify({'success': False, 'message': 'AI 未返回任何内容'}), 500
    except Exception as e:
        log_error('copywriter.generate', e)
        return jsonify({'success': False, 'message': f'服务器内部错误：{str(e)}'}), 500

@bp.route('/translate', methods=['POST'])
def translate():
    data = request.get_json()
    validation = validate_request(CopywriterTranslateSchema, data)
    
    if not validation['valid']:
        return jsonify({'success': False, 'errors': validation['errors']}), 400
    
    try:
        llm_service = LLMService()
        result = llm_service.translate_copywriter(
            data['title'],
            data['bullet_points'],
            data['description'],
            data['target_language']
        )
        
        if result and 'error' in result:
            return jsonify({'success': False, 'message': result['error']}), 400
        
        if result:
            return jsonify({'success': True, 'data': result})
        
        return jsonify({'success': False, 'message': 'AI 未返回任何内容'}), 500
    except Exception as e:
        log_error('copywriter.translate', e)
        return jsonify({'success': False, 'message': f'服务器内部错误：{str(e)}'}), 500


def _merchant():
    body = request.get_json(silent=True) or {}
    return body.get('merchant_id') or request.args.get('merchant_id') or DEFAULT_MERCHANT


@bp.route('/history', methods=['GET'])
def history_list():
    try:
        records = list_copywriter_records(_merchant())
        for r in records:
            if r.get('result_json'):
                try:
                    r['result'] = json.loads(r['result_json'])
                except Exception:
                    r['result'] = None
            r.pop('result_json', None)
        return jsonify({'success': True, 'data': records})
    except Exception as e:
        log_error('copywriter.history_list', e)
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/history', methods=['POST'])
def history_add():
    data = request.get_json() or {}
    try:
        rec_id = add_copywriter_record(
            _merchant(),
            data.get('mode', 'manual'),
            data.get('platform'),
            data.get('language'),
            data.get('input_text', ''),
            json.dumps(data.get('result', {}), ensure_ascii=False)
        )
        return jsonify({'success': True, 'data': {'id': rec_id}})
    except Exception as e:
        log_error('copywriter.history_add', e)
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/history/<int:rec_id>', methods=['DELETE'])
def history_delete(rec_id):
    try:
        delete_copywriter_record(_merchant(), rec_id)
        return jsonify({'success': True, 'data': {'id': rec_id}})
    except Exception as e:
        log_error('copywriter.history_delete', e)
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/history', methods=['DELETE'])
def history_clear():
    try:
        clear_copywriter_records(_merchant())
        return jsonify({'success': True, 'data': None})
    except Exception as e:
        log_error('copywriter.history_clear', e)
        return jsonify({'success': False, 'message': str(e)}), 500
