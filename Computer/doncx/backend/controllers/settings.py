from flask import Blueprint, request, jsonify
from utils.validator import SettingsUpdateSchema, validate_request
from utils.db import get_settings as db_get_settings, save_settings
from services.runtime_config import get_api_settings, mask_secret, is_masked

bp = Blueprint('settings', __name__)

DEFAULT_MERCHANT = 'default'


def _build_store_settings():
    return {
        'name': '',
        'address': '',
        'market': 'global',
        'default_language': 'en'
    }


# strict_slashes=False：/api/settings 与 /api/settings/ 都能直接命中，
# 避免 308 重定向（重定向地址在反向代理下容易被拼成 http:// 而被浏览器拦截）
@bp.route('/', methods=['GET'], strict_slashes=False)
def get_settings():
    """返回当前生效的设置：数据库值优先，缺失字段用 .env 默认值兜底"""
    db_store = db_get_settings(DEFAULT_MERCHANT, 'store')

    # 与调用大模型时使用的是同一套解析逻辑，保证界面显示 = 实际生效
    api = get_api_settings()
    # 密钥不回显明文，只返回掩码，避免接口被访问时泄露真实密钥
    api['api_key'] = mask_secret(api['api_key'])
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
    settings_data = dict(data.get('data', {}) or {})

    if category not in ('api', 'store'):
        return jsonify({'success': False, 'message': '无效的设置类型'}), 400

    # 密钥在界面上是打码回显的，前端会把掩码原样提交回来；
    # 这种情况必须保留数据库里的原密钥，否则真实密钥会被覆盖成掩码。
    if category == 'api' and is_masked(settings_data.get('api_key')):
        existing = db_get_settings(DEFAULT_MERCHANT, 'api') or {}
        if existing.get('api_key'):
            settings_data['api_key'] = existing['api_key']
        else:
            # 数据库里没有存过密钥，保持 .env 里的默认值生效
            settings_data.pop('api_key', None)

    # 保存到数据库
    save_settings(DEFAULT_MERCHANT, category, settings_data)

    return jsonify({'success': True, 'message': '设置保存成功'})
