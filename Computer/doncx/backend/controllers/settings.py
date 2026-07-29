from flask import Blueprint, request, jsonify
from utils.validator import SettingsUpdateSchema, validate_request
from config import Config
from utils.db import get_settings as db_get_settings, save_settings

bp = Blueprint('settings', __name__)

DEFAULT_MERCHANT = 'default'


def _build_api_settings():
    """从 Config（.env）构建默认 API 设置"""
    return {
        'api_key': Config.API_KEY,
        'api_endpoint': Config.API_ENDPOINT,
        'model': Config.MODEL_NAME,
        'temperature': Config.TEMPERATURE,
        'max_tokens': Config.MAX_TOKENS,
        'timeout': Config.TIMEOUT
    }


def _build_store_settings():
    return {
        'name': '',
        'address': '',
        'market': 'global',
        'default_language': 'en'
    }


@bp.route('/', methods=['GET'])
def get_settings():
    """返回合并后的设置：数据库持久化值优先，缺失字段用 .env 默认值兜底"""
    db_api = db_get_settings(DEFAULT_MERCHANT, 'api')
    db_store = db_get_settings(DEFAULT_MERCHANT, 'store')

    # 数据库值合并到默认值上（数据库值覆盖默认值）
    api = {**_build_api_settings(), **db_api}
    store = {**_build_store_settings(), **db_store}

    return jsonify({
        'success': True,
        'data': {
            'api': api,
            'store': store
        }
    })


@bp.route('/update', methods=['POST'])
def update_settings():
    data = request.get_json()
    validation = validate_request(SettingsUpdateSchema, data)

    if not validation['valid']:
        return jsonify({'success': False, 'errors': validation['errors']}), 400

    category = data.get('type')  # 'api' 或 'store'
    settings_data = data.get('data', {})

    if category not in ('api', 'store'):
        return jsonify({'success': False, 'message': '无效的设置类型'}), 400

    # 保存到数据库
    save_settings(DEFAULT_MERCHANT, category, settings_data)

    return jsonify({'success': True, 'message': '设置保存成功'})