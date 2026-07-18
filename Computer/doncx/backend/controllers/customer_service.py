import json

from flask import Blueprint, request, jsonify
from services.llm_service import LLMService
from utils.validator import CustomerServiceProcessSchema, validate_request
from utils.logger import log_error
from utils.db import (
    list_messages, add_message, get_message, update_message, delete_message,
    DEFAULT_MERCHANT
)

bp = Blueprint('customer_service', __name__)

@bp.route('/process', methods=['POST'])
def process():
    data = request.get_json()
    validation = validate_request(CustomerServiceProcessSchema, data)
    
    if not validation['valid']:
        return jsonify({'success': False, 'errors': validation['errors']}), 400
    
    llm_service = LLMService()
    result = llm_service.process_customer_service(
        data['message'],
        data['platform']
    )
    
    if result and 'error' in result:
        return jsonify({'success': False, 'message': result['error']}), 400
    
    if result:
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'message': 'Failed to process customer service'}), 500


def _merchant():
    body = request.get_json(silent=True) or {}
    return body.get('merchant_id') or request.args.get('merchant_id') or DEFAULT_MERCHANT


@bp.route('/messages', methods=['GET'])
def messages_list():
    try:
        records = list_messages(_merchant())
        return jsonify({'success': True, 'data': records})
    except Exception as e:
        log_error('customer_service.messages_list', e)
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/messages', methods=['POST'])
def messages_add():
    data = request.get_json() or {}
    try:
        msg_id = add_message(
            _merchant(),
            data.get('customer_name', '客户'),
            data.get('message', ''),
            data.get('platform', 'amazon'),
            data.get('category', 'general')
        )
        return jsonify({'success': True, 'data': {'id': msg_id}})
    except Exception as e:
        log_error('customer_service.messages_add', e)
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/messages/<int:msg_id>', methods=['PUT'])
def messages_update(msg_id):
    data = request.get_json() or {}
    try:
        update_message(
            _merchant(),
            msg_id,
            data.get('response', ''),
            data.get('response_zh', ''),
            data.get('status', 'auto_replied')
        )
        return jsonify({'success': True, 'data': {'id': msg_id}})
    except Exception as e:
        log_error('customer_service.messages_update', e)
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/messages/<int:msg_id>', methods=['DELETE'])
def messages_delete(msg_id):
    try:
        delete_message(_merchant(), msg_id)
        return jsonify({'success': True, 'data': {'id': msg_id}})
    except Exception as e:
        log_error('customer_service.messages_delete', e)
        return jsonify({'success': False, 'message': str(e)}), 500
