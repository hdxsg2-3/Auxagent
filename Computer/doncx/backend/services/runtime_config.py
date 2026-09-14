"""运行时 API 配置解析

优先级：系统设置页保存到数据库的值 > 环境变量 / .env 中的默认值。

每次调用大模型前实时读取，因此在「系统设置」里改完模型 / 温度 / max_tokens
立即生效，不需要改服务器 .env，也不需要重启服务。
"""
from config import Config
from utils.db import get_settings

DEFAULT_MERCHANT = 'default'


def _env_defaults():
    """来自 .env（环境变量）的默认值"""
    return {
        'api_key': Config.API_KEY,
        'api_endpoint': Config.API_ENDPOINT,
        'model': Config.MODEL_NAME,
        'temperature': Config.TEMPERATURE,
        'max_tokens': Config.MAX_TOKENS,
        'timeout': Config.TIMEOUT,
    }


def _coerce(key, value):
    """把数据库里存的值转成合适的类型，非法或空值返回 None 以回退默认值"""
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    try:
        if key == 'temperature':
            return float(value)
        if key in ('max_tokens', 'timeout'):
            return int(float(value))
    except (TypeError, ValueError):
        return None
    return str(value).strip()


def get_api_settings():
    """返回当前生效的 API 配置（数据库覆盖 .env 默认值）"""
    settings = _env_defaults()
    try:
        stored = get_settings(DEFAULT_MERCHANT, 'api') or {}
    except Exception:
        # 数据库不可读时退回 .env 默认值，不影响主流程
        stored = {}

    if isinstance(stored, dict):
        for key in settings:
            if key in stored:
                value = _coerce(key, stored[key])
                if value is not None:
                    settings[key] = value
    return settings
