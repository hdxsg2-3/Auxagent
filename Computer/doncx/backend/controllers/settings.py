from flask import Blueprint, request, jsonify
from utils.validator import SettingsUpdateSchema, validate_request
from config import Config

bp = Blueprint('settings', __name__)

settings_store = {
    'api': {
        'api_key': Config.API_KEY,
        'api_endpoint': Config.API_ENDPOINT,
        'model': Config.MODEL_NAME,
        'temperature': Config.TEMPERATURE,
        'max_tokens': Config.MAX_TOKENS,
        'timeout': Config.TIMEOUT
    },
    'store': {
        'name': '',
        'address': '',
        'market': 'global',
        'default_language': 'en'
    }
}

@bp.route('/', methods=['GET'])
def get_settings():
    return jsonify({'success': True, 'data': settings_store})

@bp.route('/update', methods=['POST'])
def update_settings():
    data = request.get_json()
    validation = validate_request(SettingsUpdateSchema, data)
    
    if not validation['valid']:
        return jsonify({'success': False, 'errors': validation['errors']}), 400
    
    try:
        settings_store[data['type']].update(data['data'])
        return jsonify({'success': True, 'message': 'Settings updated successfully'})
    except KeyError:
        return jsonify({'success': False, 'message': 'Invalid settings type'}), 400
