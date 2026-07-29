"""多平台电商 API 适配器抽象层。

目前内置：
- amazon：Amazon Selling Partner API (SP-API) 适配器
- temu：Temu 开放平台/卖家 API 适配器
- ebay：eBay 开放平台适配器（免费 Sandbox 真实上架，0 月租）

设计原则：
- 所有适配器统一实现 BasePlatform 接口。
- 默认启用 mock 模式：只要店铺凭证里没有显式关闭 mock 或缺少关键密钥，就返回模拟数据，
  保证项目无真实平台权限时也能完整演示全自动链路。
- 当用户申请到真实开发者权限并填写完整凭证后，mock 自动关闭，调用真实平台接口。
"""
import json
from abc import ABC, abstractmethod


class BasePlatform(ABC):
    PLATFORM = ''

    def __init__(self, shop_id, credentials, mock=False):
        self.shop_id = shop_id
        self.credentials = credentials or {}
        self.mock = mock

    @abstractmethod
    def test_connection(self):
        """测试店铺 API 连接是否可用。"""
        pass

    @abstractmethod
    def list_products(self, **kwargs):
        """拉取店铺在售商品列表。"""
        pass

    @abstractmethod
    def create_listing(self, payload):
        """创建/上架 Listing。payload 通常包含 sku、title、bullet_points、description 等。"""
        pass

    @abstractmethod
    def get_messages(self, **kwargs):
        """拉取买家站内消息。"""
        pass

    @abstractmethod
    def send_message(self, payload):
        """发送站内消息给买家。"""
        pass

    def _log_args(self, action, **kwargs):
        """辅助：把调用参数安全序列化（不打印敏感字段）。"""
        safe = {}
        for k, v in kwargs.items():
            if any(s in k.lower() for s in ('secret', 'key', 'token', 'password')):
                safe[k] = '***'
            else:
                safe[k] = v
        return {'shop_id': self.shop_id, 'platform': self.PLATFORM, 'action': action, 'args': safe}
