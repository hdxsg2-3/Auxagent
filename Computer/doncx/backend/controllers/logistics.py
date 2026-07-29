import time
import json
from flask import Blueprint, request, jsonify
from utils.validator import (
    LogisticsGenerateSchema,
    LogisticsStatusUpdateSchema,
    LogisticsTrackingAddSchema,
    validate_request,
)
from utils.db import (
    add_logistics_document,
    list_logistics_documents,
    get_logistics_document,
    update_logistics_document,
    add_logistics_tracking,
    list_logistics_tracking,
    DEFAULT_MERCHANT,
)

bp = Blueprint('logistics', __name__)


@bp.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    validation = validate_request(LogisticsGenerateSchema, data)

    if not validation['valid']:
        return jsonify({'success': False, 'errors': validation['errors']}), 400

    try:
        items = data.get('items', [])
        total_amount = sum(
            item.get('quantity', 0) * item.get('unit_price', 0) for item in items
        )
        totals = {
            'total_packages': data.get('total_packages', 0),
            'total_weight': data.get('total_weight', 0),
            'total_amount': round(total_amount, 2),
        }

        doc_id = add_logistics_document(
            merchant_id=DEFAULT_MERCHANT,
            doc_type=data['type'],
            transport_mode=data['shipping_method'],
            shipper_info_json=json.dumps(data['sender'], ensure_ascii=False),
            consignee_info_json=json.dumps(data['receiver'], ensure_ascii=False),
            items_json=json.dumps(items, ensure_ascii=False),
            totals_json=json.dumps(totals, ensure_ascii=False),
            status='generated',
        )

        # 自动生成一条“已生成”轨迹
        add_logistics_tracking(
            document_id=doc_id,
            status='generated',
            description='物流单据已生成',
        )

        result = {
            'id': doc_id,
            'type': data['type'],
            'shipping_method': data['shipping_method'],
            'sender': data['sender'],
            'receiver': data['receiver'],
            'items': items,
            'totals': totals,
            'document_id': f'DOC-{int(time.time())}',
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'generated',
        }

        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/documents', methods=['GET'])
def get_documents():
    try:
        docs = list_logistics_documents(DEFAULT_MERCHANT)
        return jsonify({'success': True, 'data': docs})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/documents/<int:doc_id>', methods=['GET'])
def get_document(doc_id):
    try:
        doc = get_logistics_document(DEFAULT_MERCHANT, doc_id)
        if not doc:
            return jsonify({'success': False, 'message': '单据不存在'}), 404
        doc['tracking'] = list_logistics_tracking(doc_id)
        return jsonify({'success': True, 'data': doc})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/documents/<int:doc_id>/status', methods=['POST'])
def update_status(doc_id):
    data = request.get_json() or {}
    validation = validate_request(LogisticsStatusUpdateSchema, data)
    if not validation['valid']:
        return jsonify({'success': False, 'errors': validation['errors']}), 400

    try:
        doc = get_logistics_document(DEFAULT_MERCHANT, doc_id)
        if not doc:
            return jsonify({'success': False, 'message': '单据不存在'}), 404

        update_fields = {'status': data['status']}
        if 'tracking_number' in data:
            update_fields['tracking_number'] = data['tracking_number']
        if 'carrier' in data:
            update_fields['carrier'] = data['carrier']

        update_logistics_document(DEFAULT_MERCHANT, doc_id, **update_fields)

        # 记录状态变更轨迹
        description = f"单据状态更新为：{data['status']}"
        if data.get('tracking_number'):
            description += f"，运单号：{data['tracking_number']}"
        if data.get('carrier'):
            description += f"，承运商：{data['carrier']}"
        add_logistics_tracking(
            document_id=doc_id,
            status=data['status'],
            description=description,
        )

        return jsonify({'success': True, 'message': '状态已更新'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/documents/<int:doc_id>/tracking', methods=['GET'])
def get_tracking(doc_id):
    try:
        doc = get_logistics_document(DEFAULT_MERCHANT, doc_id)
        if not doc:
            return jsonify({'success': False, 'message': '单据不存在'}), 404
        tracking = list_logistics_tracking(doc_id)
        return jsonify({'success': True, 'data': tracking})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/documents/<int:doc_id>/tracking', methods=['POST'])
def add_tracking(doc_id):
    data = request.get_json() or {}
    validation = validate_request(LogisticsTrackingAddSchema, data)
    if not validation['valid']:
        return jsonify({'success': False, 'errors': validation['errors']}), 400

    try:
        doc = get_logistics_document(DEFAULT_MERCHANT, doc_id)
        if not doc:
            return jsonify({'success': False, 'message': '单据不存在'}), 404

        tracking_id = add_logistics_tracking(
            document_id=doc_id,
            status=data['status'],
            location=data.get('location', ''),
            description=data.get('description', ''),
        )

        # 同步更新单据最新状态
        update_logistics_document(DEFAULT_MERCHANT, doc_id, status=data['status'])

        return jsonify({'success': True, 'data': {'id': tracking_id}})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
