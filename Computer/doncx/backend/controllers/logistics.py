import time
from flask import Blueprint, request, jsonify
from utils.validator import LogisticsGenerateSchema, validate_request

bp = Blueprint('logistics', __name__)

@bp.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    validation = validate_request(LogisticsGenerateSchema, data)
    
    if not validation['valid']:
        return jsonify({'success': False, 'errors': validation['errors']}), 400
    
    try:
        total_amount = sum(item.get('quantity', 0) * item.get('unit_price', 0) for item in data.get('items', []))
        
        result = {
            'type': data['type'],
            'shipping_method': data['shipping_method'],
            'sender': data['sender'],
            'receiver': data['receiver'],
            'items': data['items'],
            'total_packages': data.get('total_packages', 0),
            'total_weight': data.get('total_weight', 0),
            'total_amount': round(total_amount, 2),
            'document_id': f'DOC-{int(time.time())}',
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
