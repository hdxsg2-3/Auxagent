import json

from flask import Blueprint, request, jsonify
from services.llm_service import LLMService
from utils.validator import ComplianceScanSchema, validate_request
from utils.logger import log_error
from utils.db import (
    list_compliance_records, add_compliance_record,
    delete_compliance_record, clear_compliance_records, DEFAULT_MERCHANT
)

bp = Blueprint('compliance', __name__)

@bp.route('/scan', methods=['POST'])
def scan():
    data = request.get_json()
    validation = validate_request(ComplianceScanSchema, data)
    
    if not validation['valid']:
        return jsonify({'success': False, 'errors': validation['errors']}), 400
    
    llm_service = LLMService()
    result = llm_service.scan_compliance(
        data['content'],
        data.get('check_extreme_words', True),
        data.get('check_copyright', True),
        data.get('check_forbidden_words', True)
    )
    
    if result and 'error' in result:
        return jsonify({'success': False, 'message': result['error']}), 400
    
    if result:
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'message': 'Failed to scan compliance'}), 500


def _merchant():
    body = request.get_json(silent=True) or {}
    return body.get('merchant_id') or request.args.get('merchant_id') or DEFAULT_MERCHANT


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
            json.dumps(data.get('result', {}), ensure_ascii=False)
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
