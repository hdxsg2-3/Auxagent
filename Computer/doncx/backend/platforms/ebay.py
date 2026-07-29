import base64
import json
import time
import requests
import xml.etree.ElementTree as ET
from .base import BasePlatform


def _esc_xml(text):
    """XML 转义特殊字符。"""
    if not text:
        return ''
    return (str(text)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&apos;'))


def _parse_trading_response(xml_text):
    """解析 Trading API 的 XML 响应，提取 Ack / Errors / 数据。"""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return {'ack': 'Failure', 'errors': [{'short_message': 'XML parse error'}]}

    ns = {'e': 'urn:ebay:apis:eBLBaseComponents'}
    ack = root.find('e:Ack', ns)
    ack_text = ack.text if ack is not None else 'Failure'

    errors = []
    for err in root.findall('e:Errors', ns):
        short_msg = err.find('e:ShortMessage', ns)
        long_msg = err.find('e:LongMessage', ns)
        errors.append({
            'short_message': short_msg.text if short_msg is not None else '',
            'long_message': long_msg.text if long_msg is not None else '',
        })

    return {'ack': ack_text, 'errors': errors, 'root': root}


class EbayPlatform(BasePlatform):
    """eBay 适配器（Sandbox / Production 通用）。

    使用 Trading XML API（AddItem / GetMyMessages / SendMessage），
    完全兼容 Auth'n'Auth Token，无需 OAuth 2.0 配置。

    免费方案：在 https://developer.ebay.com 免费注册开发者，创建 Sandbox 测试用户，
    用「OAuth Token Generator → Auth'n'Auth」生成 User Token，即可真实上架、
    真实拉取消息、真实发送回复——全程 0 月租。

    所需凭证（JSON）：
    - client_id, client_secret, dev_id  开发者后台 Application Keys
    - user_token                       Auth'n'Auth Token（从 eBay 开发者后台复制）
    - marketplace_id                   可选，默认 EBAY_US
    - region                           可选，us/uk/de... 用来推断 marketplace_id
    - sandbox                          默认 true，走 sandbox 接口；false 走生产
    - category_id                      可选，上架类目；不填用默认 '30022'
    - mock                             true 时返回模拟数据，不真实调用
    """
    PLATFORM = 'ebay'

    MARKETPLACE_IDS = {
        'us': 'EBAY_US', 'uk': 'EBAY_GB', 'de': 'EBAY_DE',
        'fr': 'EBAY_FR', 'au': 'EBAY_AU', 'ca': 'EBAY_CA',
        'it': 'EBAY_IT', 'es': 'EBAY_ES',
    }

    def __init__(self, shop_id, credentials, mock=False):
        super().__init__(shop_id, credentials, mock)
        self.client_id = credentials.get('client_id', '')
        self.client_secret = credentials.get('client_secret', '')
        self.dev_id = credentials.get('dev_id', '')
        self.user_token = credentials.get('user_token', '')
        self.region = (credentials.get('region') or 'us').lower()
        self.marketplace_id = credentials.get('marketplace_id') or self.MARKETPLACE_IDS.get(self.region, 'EBAY_US')
        self.sandbox = credentials.get('sandbox', True)
        self.category_id = credentials.get('category_id') or '30022'
        self.base_url = 'https://api.sandbox.ebay.com' if self.sandbox else 'https://api.ebay.com'

        if not self.mock:
            if not all([self.client_id, self.client_secret, self.user_token]):
                self.mock = True

    # ---------- Trading API 底层 ----------
    def _trading_request(self, call_name, xml_body):
        """调用 eBay Trading XML API，兼容 Auth'n'Auth Token。"""
        url = 'https://api.sandbox.ebay.com/ws/api.dll' if self.sandbox else 'https://api.ebay.com/ws/api.dll'
        headers = {
            'X-EBAY-API-CALL-NAME': call_name,
            'X-EBAY-API-COMPATIBILITY-LEVEL': '1199',
            'X-EBAY-API-SITEID': '0',
            'X-EBAY-API-DEV-NAME': self.dev_id or '',
            'X-EBAY-API-APP-NAME': self.client_id,
            'X-EBAY-API-CERT-NAME': self.client_secret,
            'Content-Type': 'text/xml',
        }
        resp = requests.post(url, headers=headers, data=xml_body, timeout=30)
        return resp

    def _build_auth_xml(self):
        return f'''<RequesterCredentials>
    <eBayAuthToken>{self.user_token}</eBayAuthToken>
</RequesterCredentials>'''

    # ---------- 接口实现 ----------
    def test_connection(self):
        if self.mock:
            return {'success': True, 'mock': True, 'message': 'eBay 模拟连接成功'}
        xml = f'''<?xml version="1.0" encoding="utf-8"?>
<GetUserRequest xmlns="urn:ebay:apis:eBLBaseComponents">
    {self._build_auth_xml()}
</GetUserRequest>'''
        resp = self._trading_request('GetUser', xml)
        parsed = _parse_trading_response(resp.text)
        if parsed['ack'] == 'Success':
            env = 'Sandbox' if self.sandbox else 'Production'
            return {'success': True, 'mock': False, 'message': f'eBay 连接成功（{env}，Trading API）'}
        elif parsed['errors'] and any('token' in e.get('short_message', '').lower() for e in parsed['errors']):
            return {'success': False, 'mock': False, 'message': 'Token 无效：请复制完整的 User Token'}
        else:
            err_msg = parsed['errors'][0].get('short_message', '') if parsed['errors'] else '未知错误'
            return {'success': False, 'mock': False, 'message': f'连接失败：{err_msg}'}

    def list_products(self, **kwargs):
        if self.mock:
            return [
                {'product_id': 'DEMO-EBAY-001', 'title': 'Demo eBay Lamp', 'price': 19.99, 'stock': 100, 'status': 'ACTIVE'},
                {'product_id': 'DEMO-EBAY-002', 'title': 'Demo eBay Mouse', 'price': 9.99, 'stock': 200, 'status': 'ACTIVE'},
            ]
        xml = f'''<?xml version="1.0" encoding="utf-8"?>
<GetMyeBaySellingRequest xmlns="urn:ebay:apis:eBLBaseComponents">
    {self._build_auth_xml()}
    <ActiveList>
        <Pagination>
            <EntriesPerPage>50</EntriesPerPage>
            <PageNumber>1</PageNumber>
        </Pagination>
    </ActiveList>
</GetMyeBaySellingRequest>'''
        resp = self._trading_request('GetMyeBaySelling', xml)
        parsed = _parse_trading_response(resp.text)
        if parsed['ack'] != 'Success':
            return []
        root = parsed['root']
        ns = {'e': 'urn:ebay:apis:eBLBaseComponents'}
        items = []
        for item in root.findall('.//e:Item/e:ItemID', ns):
            item_id = item.text
            title_el = item.find('../e:Title', ns)
            price_el = item.find('../e:SellingStatus/e:CurrentPrice', ns)
            qty_el = item.find('../e:QuantityAvailable', ns)
            items.append({
                'product_id': item_id,
                'title': title_el.text if title_el is not None else '',
                'price': float(price_el.text) if price_el is not None else 0.0,
                'stock': int(qty_el.text) if qty_el is not None else 0,
                'status': 'ACTIVE',
            })
        return items

    def create_listing(self, payload):
        """使用 Trading API AddItem 上架商品。返回 eBay Item ID。"""
        if self.mock:
            return {
                'success': True, 'mock': True,
                'item_id': f'mock-ebay-{int(time.time())}',
                'sku': payload.get('sku'),
                'status': 'PUBLISHED',
                'message': 'eBay Listing 模拟提交成功'
            }
        sku = payload.get('sku') or f'SKU-{int(time.time())}'
        title = payload.get('title', 'Demo Product')
        description = payload.get('description', '')
        bullet_points = payload.get('bullet_points') or []
        # 合并 bullet points 到描述
        if bullet_points:
            desc_lines = description.split('\n') if description else []
            desc_lines.append('')
            desc_lines.append('Features:')
            for bp in bullet_points:
                desc_lines.append(f'- {bp}')
            description = '\n'.join(desc_lines)

        price = payload.get('price') or 0.0
        stock = payload.get('stock') or 0
        images = payload.get('images') or []
        category_id = payload.get('category_id') or self.category_id

        # 图片 XML
        pic_xml = ''
        if images:
            pic_urls = '\n'.join(f'<PictureURL>{_esc_xml(url)}</PictureURL>' for url in images[:12])
            pic_xml = f'<PictureDetails>{pic_urls}</PictureDetails>'

        xml = f'''<?xml version="1.0" encoding="utf-8"?>
<AddItemRequest xmlns="urn:ebay:apis:eBLBaseComponents">
    {self._build_auth_xml()}
    <Item>
        <Title>{_esc_xml(title)}</Title>
        <Description>{_esc_xml(description)}</Description>
        <PrimaryCategory><CategoryID>{category_id}</CategoryID></PrimaryCategory>
        <StartPrice>{price}</StartPrice>
        <Quantity>{stock}</Quantity>
        <ConditionID>1000</ConditionID>
        <CategoryMappingAllowed>true</CategoryMappingAllowed>
        <Country>US</Country>
        <Currency>USD</Currency>
        <ListingDuration>GTC</ListingDuration>
        <ListingType>FixedPriceItem</ListingType>
        <Location>San Jose</Location>
        <PostalCode>95125</PostalCode>
        <DispatchTimeMax>3</DispatchTimeMax>
        <ShippingDetails>
            <ShippingType>Flat</ShippingType>
            <ShippingServiceOptions>
                <ShippingService>USPSMedia</ShippingService>
                <ShippingServiceCost currencyID="USD">0.0</ShippingServiceCost>
                <ShippingServicePriority>1</ShippingServicePriority>
                <FreeShipping>true</FreeShipping>
            </ShippingServiceOptions>
        </ShippingDetails>
        <ReturnPolicy>
            <ReturnsAcceptedOption>ReturnsAccepted</ReturnsAcceptedOption>
            <RefundOption>MoneyBack</RefundOption>
            <ReturnsWithinOption>Days_30</ReturnsWithinOption>
            <ShippingCostPaidByOption>Buyer</ShippingCostPaidByOption>
        </ReturnPolicy>
        {pic_xml}
    </Item>
</AddItemRequest>'''

        resp = self._trading_request('AddItem', xml)
        parsed = _parse_trading_response(resp.text)
        if parsed['ack'] in ('Success', 'Warning'):
            root = parsed['root']
            ns = {'e': 'urn:ebay:apis:eBLBaseComponents'}
            item_id = root.find('e:ItemID', ns)
            item_id_text = item_id.text if item_id is not None else ''
            return {
                'success': True, 'mock': False,
                'item_id': item_id_text, 'sku': sku,
                'status': 'PUBLISHED',
                'message': f'eBay 上架成功，Item ID: {item_id_text}'
            }
        else:
            err_msg = parsed['errors'][0].get('short_message', '') if parsed['errors'] else '未知错误'
            return {'success': False, 'mock': False, 'message': f'eBay 上架失败：{err_msg}'}

    def get_messages(self, **kwargs):
        if self.mock:
            return [
                {'message_id': 'DEMO-EB-001', 'buyer_name': 'eBay Buyer A', 'order_id': 'E-123456', 'content': 'Is this still available?', 'created_at': '2026-07-19T10:00:00Z'},
                {'message_id': 'DEMO-EB-002', 'buyer_name': 'eBay Buyer B', 'order_id': 'E-123457', 'content': 'Can you ship faster?', 'created_at': '2026-07-19T11:00:00Z'},
            ]
        xml = f'''<?xml version="1.0" encoding="utf-8"?>
<GetMyMessagesRequest xmlns="urn:ebay:apis:eBLBaseComponents">
    {self._build_auth_xml()}
    <DetailLevel>ReturnMessages</DetailLevel>
    <FolderID>0</FolderID>
    <Pagination>
        <EntriesPerPage>20</EntriesPerPage>
        <PageNumber>1</PageNumber>
    </Pagination>
</GetMyMessagesRequest>'''
        resp = self._trading_request('GetMyMessages', xml)
        parsed = _parse_trading_response(resp.text)
        if parsed['ack'] != 'Success':
            return []
        root = parsed['root']
        ns = {'e': 'urn:ebay:apis:eBLBaseComponents'}
        messages = []
        for msg in root.findall('.//e:MemberMessage', ns):
            msg_id_el = msg.find('e:MessageID', ns)
            sender_el = msg.find('e:SenderID', ns)
            subject_el = msg.find('e:Subject', ns)
            body_el = msg.find('e:Body', ns)
            item_id_el = msg.find('e:ItemID', ns)
            messages.append({
                'message_id': msg_id_el.text if msg_id_el is not None else '',
                'buyer_name': sender_el.text if sender_el is not None else 'Unknown',
                'order_id': item_id_el.text if item_id_el is not None else '',
                'content': f"{subject_el.text or ''}: {body_el.text or ''}",
                'created_at': '',
            })
        return messages

    def send_message(self, payload):
        if self.mock:
            return {'success': True, 'mock': True, 'message_id': f'mock-eb-{int(time.time())}', 'status': 'SENT'}
        item_id = payload.get('order_id') or payload.get('item_id') or payload.get('conversation_id')
        buyer_id = payload.get('buyer_id') or 'buyer'
        text = payload.get('text', '')
        if not item_id:
            return {'success': False, 'mock': False, 'message': '发送失败：缺少 item_id / order_id'}
        xml = f'''<?xml version="1.0" encoding="utf-8"?>
<AddMemberMessageAAQToPartnerRequest xmlns="urn:ebay:apis:eBLBaseComponents">
    {self._build_auth_xml()}
    <ItemID>{item_id}</ItemID>
    <MemberMessage>
        <Subject>Re: Order</Subject>
        <Body>{_esc_xml(text)}</Body>
        <QuestionType>General</QuestionType>
        <RecipientID>{_esc_xml(buyer_id)}</RecipientID>
    </MemberMessage>
</AddMemberMessageAAQToPartnerRequest>'''
        resp = self._trading_request('AddMemberMessageAAQToPartner', xml)
        parsed = _parse_trading_response(resp.text)
        if parsed['ack'] == 'Success':
            return {'success': True, 'mock': False, 'status': 'SENT', 'message': 'eBay 消息已发送'}
        else:
            err_msg = parsed['errors'][0].get('short_message', '') if parsed['errors'] else '未知错误'
            return {'success': False, 'mock': False, 'message': f'发送失败：{err_msg}'}
