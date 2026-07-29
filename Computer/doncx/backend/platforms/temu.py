import hashlib
import json
import time
import requests
from .base import BasePlatform


class TemuPlatform(BasePlatform):
    """Temu 开放平台 / 卖家 API 适配器。

    真实对接所需资料（需在 Temu 商家后台/开放平台申请）：
    - app_key / app_secret
    - access_token（店铺授权后获得）
    - region（global 等）
    """
    PLATFORM = 'temu'

    def __init__(self, shop_id, credentials, mock=False):
        super().__init__(shop_id, credentials, mock)
        self.app_key = credentials.get('app_key', '')
        self.app_secret = credentials.get('app_secret', '')
        self.access_token = credentials.get('access_token', '')
        self.region = credentials.get('region', 'global')

        if not self.mock:
            if not all([self.app_key, self.app_secret, self.access_token]):
                self.mock = True

    def _sign(self, params):
        """通用参数签名：参数排序 + appSecret 后取 MD5 大写。"""
        params = dict(params)
        params['app_key'] = self.app_key
        params['timestamp'] = int(time.time())
        items = sorted(params.items())
        sign_str = ''.join(f'{k}{v}' for k, v in items) + self.app_secret
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()

    def _request(self, method, api_name, params=None, data=None):
        if self.mock:
            raise RuntimeError('Cannot call real API in mock mode')
        base_url = 'https://openapi.temu.com'
        if not params:
            params = {}
        params['app_key'] = self.app_key
        params['access_token'] = self.access_token
        params['timestamp'] = int(time.time())
        params['sign'] = self._sign(params)
        url = f'{base_url}{api_name}'
        if method == 'GET':
            return requests.get(url, params=params, timeout=30)
        return requests.post(url, params=params, json=data, timeout=30)

    def test_connection(self):
        if self.mock:
            return {'success': True, 'mock': True, 'message': 'Temu 模拟连接成功'}
        resp = self._request('GET', '/api/shop/getShopInfo')
        resp.raise_for_status()
        return {'success': True, 'mock': False, 'data': resp.json()}

    def list_products(self, **kwargs):
        if self.mock:
            return [
                {'product_id': 'DEMO-PID-001', 'title': 'Demo Temu Lamp', 'price': 12.99, 'stock': 500},
                {'product_id': 'DEMO-PID-002', 'title': 'Demo Temu Mouse', 'price': 8.99, 'stock': 1000},
            ]
        resp = self._request('GET', '/api/products/list', params={'page': 1, 'page_size': 20})
        return resp.json()

    def create_listing(self, payload):
        """上架商品。payload 包含 sku、title、description、price、stock、images 等。"""
        if self.mock:
            return {
                'success': True,
                'mock': True,
                'submission_id': f'mock-temu-{int(time.time())}',
                'sku': payload.get('sku'),
                'status': 'ACCEPTED',
                'message': 'Temu Listing 模拟提交成功'
            }
        data = {
            'title': payload.get('title'),
            'description': payload.get('description'),
            'images': payload.get('images', []),
            'skus': [{
                'sku': payload.get('sku'),
                'price': payload.get('price', 0),
                'stock': payload.get('stock', 0)
            }]
        }
        resp = self._request('POST', '/api/products/create', data=data)
        return {'success': True, 'status_code': resp.status_code, 'data': resp.json()}

    def get_messages(self, **kwargs):
        if self.mock:
            return [
                {'message_id': 'DEMO-TM-001', 'buyer_name': 'Temu Buyer A', 'order_id': 'T-123456', 'content': 'Can I get a discount?', 'created_at': '2026-07-19T10:00:00Z'},
                {'message_id': 'DEMO-TM-002', 'buyer_name': 'Temu Buyer B', 'order_id': 'T-123457', 'content': 'When will it be shipped?', 'created_at': '2026-07-19T11:00:00Z'},
            ]
        resp = self._request('GET', '/api/message/list', params={'page': 1, 'page_size': 20})
        return resp.json()

    def send_message(self, payload):
        if self.mock:
            return {
                'success': True,
                'mock': True,
                'message_id': f'mock-tm-{int(time.time())}',
                'status': 'SENT'
            }
        data = {
            'order_id': payload.get('order_id'),
            'buyer_id': payload.get('buyer_id'),
            'content': payload.get('text')
        }
        resp = self._request('POST', '/api/message/send', data=data)
        return {'success': True, 'status_code': resp.status_code, 'data': resp.json()}
