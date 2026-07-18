"""
火山引擎 V4 签名工具（HMAC-SHA256）

火山引擎 OpenAPI 统一使用 AWS SigV4 风格的鉴权，区别是必须额外对请求体做
sha256 并放入 `x-content-sha256` 参与签名。本模块供机器翻译、内容安全等
需要 AK/SK 签名的产品调用，方舟大模型（Bearer Token）不需要它。
"""
import hmac
import hashlib
import datetime
from urllib.parse import quote


def _sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def _hmac(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()


def _hmac_hex(key: bytes, msg: str) -> str:
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).hexdigest()


class VolcSigner:
    def __init__(self, ak: str, sk: str):
        self.ak = ak
        self.sk = sk

    def sign(self, method: str, host: str, region: str, service: str,
             path: str = '/', query_params: dict = None, body: str = '',
             date: datetime.datetime = None):
        """
        生成签名所需的请求头，并返回带 query 的完整 URL 路径后缀。

        返回: (headers: dict, query_string: str)
          headers 已包含 Authorization / X-Date / X-Content-Sha256 / Content-Type / Host
          query_string 为规范化的 query（不含前导 ?），调用方拼到 URL 上
        """
        if date is None:
            date = datetime.datetime.utcnow()
        x_date = date.strftime('%Y%m%dT%H%M%SZ')
        short_date = date.strftime('%Y%m%d')

        payload_hash = _sha256_hex(body)

        # 规范化 query（按 key 排序并 URL 编码）
        qp = query_params or {}
        canonical_query = '&'.join(
            f'{quote(k, safe="")}={quote(str(v), safe="")}'
            for k, v in sorted(qp.items())
        )

        # 待签名 header（按 key 排序）
        unsigned = {
            'content-type': 'application/json',
            'host': host,
            'x-content-sha256': payload_hash,
            'x-date': x_date,
        }
        signed_headers = ';'.join(sorted(unsigned.keys()))
        canonical_headers = ''.join(
            f'{k}:{unsigned[k]}\n' for k in sorted(unsigned.keys())
        )

        canonical_request = '\n'.join([
            method.upper(),
            path,
            canonical_query,
            canonical_headers,
            signed_headers,
            payload_hash,
        ])

        credential_scope = f'{short_date}/{region}/{service}/request'
        string_to_sign = '\n'.join([
            'HMAC-SHA256',
            x_date,
            credential_scope,
            _sha256_hex(canonical_request),
        ])

        k_date = _hmac(self.sk.encode('utf-8'), short_date)
        k_region = _hmac(k_date, region)
        k_service = _hmac(k_region, service)
        k_signing = _hmac(k_service, 'request')
        signature = _hmac_hex(k_signing, string_to_sign)

        authorization = (
            f'HMAC-SHA256 Credential={self.ak}/{credential_scope}, '
            f'SignedHeaders={signed_headers}, Signature={signature}'
        )

        headers = dict(unsigned)
        headers['Authorization'] = authorization
        return headers, canonical_query
