from flask import Blueprint, request, jsonify
from services.llm_service import LLMService
from utils.validator import LegalSearchSchema, validate_request

bp = Blueprint('legal', __name__)

@bp.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    validation = validate_request(LegalSearchSchema, data)
    
    if not validation['valid']:
        return jsonify({'success': False, 'errors': validation['errors']}), 400
    
    llm_service = LLMService()
    result = llm_service.search_legal(
        data['query'],
        data.get('regions', ['EU', 'US'])
    )
    
    if result and 'error' in result:
        return jsonify({'success': False, 'message': result['error']}), 400
    
    if result:
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'message': 'Failed to search legal'}), 500
