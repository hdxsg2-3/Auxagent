import json
from .base import BasePlatform
from .amazon import AmazonPlatform
from .temu import TemuPlatform
from .ebay import EbayPlatform
from .local_shop import LocalShopPlatform

PLATFORM_CLASSES = {
    'amazon': AmazonPlatform,
    'temu': TemuPlatform,
    'ebay': EbayPlatform,
    'local-shop': LocalShopPlatform,
}

# 所有支持的平台（含浏览器自动化兜底支持的平台）
BROWSER_FALLBACK_PLATFORMS = ['amazon', 'ebay', 'temu']


def get_platform(shop):
    """根据 shop 记录（dict）返回对应的平台适配器实例。
    shop 字段：id, platform, name, region, credentials_json, status
    """
    platform = (shop.get('platform') or '').lower()
    cls = PLATFORM_CLASSES.get(platform)
    if not cls:
        raise ValueError(f'Unsupported platform: {platform}')

    credentials = {}
    try:
        credentials = json.loads(shop.get('credentials_json') or '{}')
    except Exception:
        credentials = {}

    # 默认开启 mock：只有显式 credentials['mock'] == False 且关键字段齐全才走真实接口
    mock = credentials.get('mock', True)
    return cls(shop['id'], credentials, mock=mock)
