import json
import time
import requests
from .base import BasePlatform


class AmazonPlatform(BasePlatform):
    """Amazon Selling Partner API (SP-API) 适配器。

    真实对接所需资料（需在 Amazon Developer Console 申请）：
    - seller_id（卖家编号，14 位）
    - refresh_token（店铺 OAuth 授权后获得）
    - client_id / client_secret（SP-API 应用凭证）
    - aws_access_key / aws_secret_key（AWS IAM 用户密钥）
    - role_arn（允许 SP-API 调用的 IAM Role ARN）
    - region / marketplace_id（如 na / ATVPDKIKX0DER）
    """
    PLATFORM = 'amazon'

    _ENDPOINTS = {
        'na': {'aws_region': 'us-east-1', 'host': 'sellingpartnerapi-na.amazon.com'},
        'eu': {'aws_region': 'eu-west-1', 'host': 'sellingpartnerapi-eu.amazon.com'},
        'fe': {'aws_region': 'us-west-2', 'host': 'sellingpartnerapi-fe.amazon.com'},
    }

    def __init__(self, shop_id, credentials, mock=False):
        super().__init__(shop_id, credentials, mock)
        self.seller_id = credentials.get('seller_id', '')
        self.refresh_token = credentials.get('refresh_token', '')
        self.client_id = credentials.get('client_id', '')
        self.client_secret = credentials.get('client_secret', '')
        self.aws_access_key = credentials.get('aws_access_key', '')
        self.aws_secret_key = credentials.get('aws_secret_key', '')
        self.role_arn = credentials.get('role_arn', '')

        region_key = (credentials.get('region') or 'na').lower()
        ep = self._ENDPOINTS.get(region_key, self._ENDPOINTS['na'])
        self.aws_region = ep['aws_region']
        self.host = ep['host']
        self.marketplace_id = credentials.get('marketplace_id', 'ATVPDKIKX0DER')

        self._access_token = None
        self._token_expires_at = 0
        self._aws_credentials = None
        self._aws_creds_expires_at = 0

        # 缺少任一关键真实凭证时自动降级为 mock 模式，避免报错
        if not self.mock:
            required = [self.refresh_token, self.client_id, self.client_secret,
                        self.aws_access_key, self.aws_secret_key, self.role_arn, self.seller_id]
            if not all(required):
                self.mock = True

    def _get_access_token(self):
        if self._access_token and self._token_expires_at > time.time():
            return self._access_token
        url = 'https://api.amazon.com/auth/o2/token'
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'sellingpartnerapi::migration'
        }
        resp = requests.post(url, data=data, timeout=30)
        resp.raise_for_status()
        token = resp.json()
        self._access_token = token['access_token']
        self._token_expires_at = time.time() + token.get('expires_in', 3600) - 60
        return self._access_token

    def _get_aws_credentials(self):
        if self._aws_credentials and self._aws_creds_expires_at > time.time():
            return self._aws_credentials
        try:
            import boto3
            sts = boto3.client(
                'sts',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )
            assumed = sts.assume_role(
                RoleArn=self.role_arn,
                RoleSessionName='sp-api-session'
            )
            creds = assumed['Credentials']
            self._aws_credentials = {
                'AccessKeyId': creds['AccessKeyId'],
                'SecretAccessKey': creds['SecretAccessKey'],
                'SessionToken': creds['SessionToken']
            }
            self._aws_creds_expires_at = time.time() + 900 - 60
            return self._aws_credentials
        except Exception as e:
            raise RuntimeError(f'STS AssumeRole failed: {e}')

    def _request(self, method, path, data=None, params=None):
        if self.mock:
            raise RuntimeError('Cannot call real API in mock mode')
        from botocore.auth import SigV4Auth
        from botocore.awsrequest import AWSRequest
        from botocore.credentials import Credentials

        access_token = self._get_access_token()
        aws = self._get_aws_credentials()

        url = f'https://{self.host}{path}'
        if params:
            req = requests.Request('GET', url, params=params)
            url = req.prepare().url

        body = json.dumps(data) if data else ''
        request = AWSRequest(method=method, url=url, data=body)
        request.headers['Content-Type'] = 'application/json'
        request.headers['x-amz-access-token'] = access_token
        request.headers['x-amz-security-token'] = aws['SessionToken']

        creds = Credentials(aws['AccessKeyId'], aws['SecretAccessKey'], aws['SessionToken'])
        SigV4Auth(creds, 'execute-api', self.aws_region).add_auth(request)

        prepared = request.prepare()
        resp = requests.request(
            prepared.method, prepared.url,
            headers=dict(prepared.headers), data=body, timeout=30
        )
        return resp

    def test_connection(self):
        if self.mock:
            return {'success': True, 'mock': True, 'message': 'Amazon 模拟连接成功'}
        # 真实：获取卖家参与的市场，验证凭证
        resp = self._request('GET', '/sellers/v1/marketplaceParticipations')
        resp.raise_for_status()
        return {'success': True, 'mock': False, 'data': resp.json()}

    def list_products(self, **kwargs):
        if self.mock:
            return [
                {'sku': 'DEMO-SKU-001', 'asin': 'B00DEMO001', 'title': 'Demo LED Desk Lamp', 'price': 29.99, 'quantity': 100},
                {'sku': 'DEMO-SKU-002', 'asin': 'B00DEMO002', 'title': 'Demo Wireless Mouse', 'price': 15.99, 'quantity': 200},
            ]
        # 真实示例：使用 Listings Items API 查询某个 SKU（实际可用 Reports API 批量拉取）
        sku = kwargs.get('sku', 'DEMO-SKU')
        resp = self._request(
            'GET',
            f'/listings/2021-08-01/items/{self.seller_id}/{sku}',
            params={'marketplaceIds': self.marketplace_id}
        )
        return resp.json()

    def create_listing(self, payload):
        """上架 Listing。payload 应包含 sku、title、bullet_points、description、product_type 等。"""
        if self.mock:
            return {
                'success': True,
                'mock': True,
                'submission_id': f'mock-sub-{int(time.time())}',
                'sku': payload.get('sku'),
                'status': 'ACCEPTED',
                'message': 'Amazon Listing 模拟提交成功'
            }
        sku = payload.get('sku')
        body = {
            'productType': payload.get('product_type', 'LAMP'),
            'requirements': 'LISTING',
            'attributes': {
                'item_name': [{'value': payload.get('title')}],
                'bullet_point': [{'value': b} for b in payload.get('bullet_points', [])],
                'product_description': [{'value': payload.get('description')}],
                # 更多字段按实际类目补充，如 brand、condition_type、item_type_keyword 等
            }
        }
        resp = self._request('PUT', f'/listings/2021-08-01/items/{self.seller_id}/{sku}', data=body)
        return {'success': True, 'status_code': resp.status_code, 'data': resp.json()}

    def get_messages(self, **kwargs):
        if self.mock:
            return [
                {'message_id': 'DEMO-MSG-001', 'order_id': '123-4567890-1234567', 'buyer_name': 'Amazon Buyer A', 'subject': 'Product question', 'body': 'Does this lamp support dimming?', 'created_at': '2026-07-19T10:00:00Z'},
                {'message_id': 'DEMO-MSG-002', 'order_id': '123-4567890-1234568', 'buyer_name': 'Amazon Buyer B', 'subject': 'Shipping', 'body': 'When will my order arrive?', 'created_at': '2026-07-19T11:00:00Z'},
            ]
        # 真实：SP-API Messaging API，需要 order_id
        order_id = kwargs.get('order_id')
        resp = self._request('GET', f'/messaging/v1/orders/{order_id}/messages')
        return resp.json()

    def send_message(self, payload):
        if self.mock:
            return {
                'success': True,
                'mock': True,
                'message_id': f'mock-msg-{int(time.time())}',
                'status': 'SENT'
            }
        order_id = payload.get('order_id')
        body = {'message': {'text': payload.get('text')}}
        resp = self._request('POST', f'/messaging/v1/orders/{order_id}/messages', data=body)
        return {'success': True, 'status_code': resp.status_code, 'data': resp.json()}
