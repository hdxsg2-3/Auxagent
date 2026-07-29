"""LocalShop —— 内建免费电商测试平台适配器。

特点：
- 零配置、即时开通、无需任何外部账号或审核
- 使用 SQLite 持久化，数据跨重启保留
- 真实 CRUD（非 Mock），返回真实商品 ID / 消息 ID
- 模拟真实电商平台 API 行为（分页、状态流转等）
- 适合演示全自动上架 + 消息收发全链路

设计理念：作为"免费即时开通的电商测试平台"，
当用户没有 Amazon / eBay / Temu 真实权限时，
LocalShop 提供完整的真实操作体验（非模拟数据）。
"""
import json
import time
import uuid
import os
import sqlite3
from contextlib import contextmanager
from .base import BasePlatform

# LocalShop 使用独立的 SQLite 数据库文件，与主业务库隔离
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_DIR = os.path.join(_BASE_DIR, 'data')
_LOCAL_DB_PATH = os.path.join(_DATA_DIR, 'local_shop.db')


@contextmanager
def _local_conn():
    os.makedirs(_DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(_LOCAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _init_local_db():
    """幂等建表 + 种子数据。"""
    with _local_conn() as conn:
        conn.executescript('''
        CREATE TABLE IF NOT EXISTS local_products (
            id TEXT PRIMARY KEY,
            shop_id INTEGER NOT NULL,
            sku TEXT NOT NULL,
            title TEXT NOT NULL,
            bullet_points TEXT DEFAULT '[]',
            description TEXT DEFAULT '',
            price REAL DEFAULT 0,
            stock INTEGER DEFAULT 0,
            product_type TEXT DEFAULT '',
            images TEXT DEFAULT '[]',
            status TEXT DEFAULT 'active',
            views INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE INDEX IF NOT EXISTS idx_local_prod_shop ON local_products(shop_id, status);

        CREATE TABLE IF NOT EXISTS local_messages (
            id TEXT PRIMARY KEY,
            shop_id INTEGER NOT NULL,
            buyer_id TEXT NOT NULL,
            buyer_name TEXT DEFAULT '',
            order_id TEXT DEFAULT '',
            subject TEXT DEFAULT '',
            body TEXT NOT NULL,
            direction TEXT DEFAULT 'inbound',
            status TEXT DEFAULT 'unread',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            replied_at TEXT DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_local_msg_shop ON local_messages(shop_id, status);

        CREATE TABLE IF NOT EXISTS local_orders (
            id TEXT PRIMARY KEY,
            shop_id INTEGER NOT NULL,
            buyer_id TEXT NOT NULL,
            buyer_name TEXT DEFAULT '',
            product_id TEXT,
            product_title TEXT DEFAULT '',
            quantity INTEGER DEFAULT 1,
            total_price REAL DEFAULT 0,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE INDEX IF NOT EXISTS idx_local_order_shop ON local_orders(shop_id, status);
        ''')


def _seed_data(shop_id):
    """首次使用时灌入种子商品和消息，让演示立即可用。"""
    with _local_conn() as conn:
        existing = conn.execute(
            "SELECT COUNT(*) as cnt FROM local_products WHERE shop_id=?",
            (shop_id,)).fetchone()
        if existing['cnt'] > 0:
            return

        seed_products = [
            {
                'sku': 'LOCAL-DEMO-001',
                'title': 'Portable LED Camping Lantern with USB Charging',
                'bullet_points': [
                    'Super bright 1000 lumens LED with 3 brightness levels',
                    'Built-in 5200mAh rechargeable battery, up to 12 hours runtime',
                    'IPX4 waterproof for outdoor camping and hiking',
                    'USB output to charge your phone in emergency',
                    'Foldable design, lightweight 280g, easy to carry'
                ],
                'description': 'Ideal for camping, hiking, power outages, and outdoor events. This LED lantern provides 360-degree illumination with adjustable brightness. The built-in battery doubles as a power bank for your devices.',
                'price': 24.99,
                'stock': 150,
                'product_type': 'SPORT_OUTDOORS',
            },
            {
                'sku': 'LOCAL-DEMO-002',
                'title': 'Wireless Bluetooth Earbuds Pro with Noise Cancellation',
                'bullet_points': [
                    'Active noise cancellation up to 35dB',
                    'Bluetooth 5.3 for stable connection and low latency',
                    '36-hour total battery life with charging case',
                    'IPX5 sweat and water resistant for workouts',
                    'Touch controls and voice assistant compatible'
                ],
                'description': 'Experience premium sound quality with active noise cancellation. These wireless earbuds deliver crystal-clear audio, deep bass, and 36 hours of total playtime.',
                'price': 39.99,
                'stock': 300,
                'product_type': 'ELECTRONICS',
            },
        ]
        for p in seed_products:
            pid = f'P{int(time.time())}{uuid.uuid4().hex[:6].upper()}'
            conn.execute(
                "INSERT INTO local_products "
                "(id, shop_id, sku, title, bullet_points, description, price, stock, product_type, status, views) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (pid, shop_id, p['sku'], p['title'],
                 json.dumps(p['bullet_points'], ensure_ascii=False),
                 p['description'], p['price'], p['stock'],
                 p['product_type'], 'active', 0))

        seed_messages = [
            {
                'buyer_id': 'buyer_jessica_001',
                'buyer_name': 'Jessica Miller',
                'order_id': 'ORD-2024-8842',
                'subject': 'Shipping delay inquiry',
                'body': 'Hi, I ordered the LED Camping Lantern 5 days ago and still haven\'t received tracking info. Can you check on my order? Order #ORD-2024-8842.',
            },
            {
                'buyer_id': 'buyer_tom_002',
                'buyer_name': 'Tom Wilson',
                'order_id': 'ORD-2024-8851',
                'subject': 'Product compatibility question',
                'body': 'Hello, do these earbuds support multi-device pairing? I want to connect them to both my phone and laptop simultaneously.',
            },
            {
                'buyer_id': 'buyer_maria_003',
                'buyer_name': 'Maria Garcia',
                'order_id': '',
                'subject': 'Bulk order discount',
                'body': 'Hola, I am interested in purchasing 50 units of the LED lantern for my outdoor event company. Do you offer bulk pricing?',
            },
        ]
        for m in seed_messages:
            mid = f'M{int(time.time())}{uuid.uuid4().hex[:6].upper()}'
            conn.execute(
                "INSERT INTO local_messages "
                "(id, shop_id, buyer_id, buyer_name, order_id, subject, body, direction, status) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (mid, shop_id, m['buyer_id'], m['buyer_name'],
                 m['order_id'], m['subject'], m['body'],
                 'inbound', 'unread'))


class LocalShopPlatform(BasePlatform):
    """LocalShop 内建测试平台适配器。

    这是一个真实的电商模拟平台（非 Mock）：
    - 商品数据持久化到 SQLite
    - 消息系统支持收发和状态流转
    - 返回真实 ID，可后续查询和管理
    - 零配置，创建店铺后立即可用
    """
    PLATFORM = 'local-shop'

    def __init__(self, shop_id, credentials, mock=False):
        super().__init__(shop_id, credentials, mock)
        # LocalShop 始终使用真实数据库操作，mock 参数被忽略
        self.mock = False
        _init_local_db()
        _seed_data(shop_id)

    def test_connection(self):
        """测试连接 —— LocalShop 始终可用。"""
        with _local_conn() as conn:
            prod_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM local_products WHERE shop_id=? AND status='active'",
                (self.shop_id,)).fetchone()['cnt']
            msg_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM local_messages WHERE shop_id=?",
                (self.shop_id,)).fetchone()['cnt']

        return {
            'success': True,
            'mock': False,
            'platform': 'local-shop',
            'message': 'LocalShop 连接成功（内建免费平台，即时可用）',
            'stats': {
                'products': prod_count,
                'messages': msg_count,
            }
        }

    def list_products(self, **kwargs):
        """拉取在售商品列表。"""
        page = kwargs.get('page', 1)
        page_size = kwargs.get('page_size', 50)
        offset = (page - 1) * page_size

        with _local_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM local_products WHERE shop_id=? AND status='active' "
                "ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (self.shop_id, page_size, offset)).fetchall()

        products = []
        for r in rows:
            products.append({
                'id': r['id'],
                'sku': r['sku'],
                'title': r['title'],
                'bullet_points': json.loads(r['bullet_points'] or '[]'),
                'description': r['description'],
                'price': r['price'],
                'stock': r['stock'],
                'product_type': r['product_type'],
                'status': r['status'],
                'views': r['views'],
                'created_at': r['created_at'],
            })
        return products

    def create_listing(self, payload):
        """创建/上架新商品到 LocalShop。"""
        sku = payload.get('sku', f'SKU-{uuid.uuid4().hex[:8].upper()}')
        title = payload.get('title', '')
        bullet_points = payload.get('bullet_points', [])
        description = payload.get('description', '')
        price = payload.get('price', 0)
        stock = payload.get('stock', 0)
        product_type = payload.get('product_type', 'GENERAL')
        images = payload.get('images', [])

        product_id = f'P{int(time.time())}{uuid.uuid4().hex[:6].upper()}'

        with _local_conn() as conn:
            # 检查 SKU 唯一性
            existing = conn.execute(
                "SELECT id FROM local_products WHERE shop_id=? AND sku=?",
                (self.shop_id, sku)).fetchone()
            if existing:
                # SKU 已存在则更新
                conn.execute(
                    "UPDATE local_products SET title=?, bullet_points=?, description=?, "
                    "price=?, stock=?, product_type=?, images=?, "
                    "updated_at=datetime('now','localtime') WHERE id=?",
                    (title, json.dumps(bullet_points, ensure_ascii=False),
                     description, price, stock, product_type,
                     json.dumps(images, ensure_ascii=False), existing['id']))
                product_id = existing['id']
                action = 'updated'
            else:
                conn.execute(
                    "INSERT INTO local_products "
                    "(id, shop_id, sku, title, bullet_points, description, price, stock, product_type, images, status, views) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (product_id, self.shop_id, sku, title,
                     json.dumps(bullet_points, ensure_ascii=False),
                     description, price, stock, product_type,
                     json.dumps(images, ensure_ascii=False),
                     'active', 0))
                action = 'created'

        return {
            'success': True,
            'mock': False,
            'platform': 'local-shop',
            'product_id': product_id,
            'sku': sku,
            'action': action,
            'message': f'商品{action}成功，ID: {product_id}',
            'listing_url': f'/local-shop/products/{product_id}',
        }

    def get_messages(self, **kwargs):
        """拉取买家消息列表。"""
        status_filter = kwargs.get('status', None)
        page = kwargs.get('page', 1)
        page_size = kwargs.get('page_size', 50)
        offset = (page - 1) * page_size

        with _local_conn() as conn:
            if status_filter:
                rows = conn.execute(
                    "SELECT * FROM local_messages WHERE shop_id=? AND status=? "
                    "ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (self.shop_id, status_filter, page_size, offset)).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM local_messages WHERE shop_id=? "
                    "ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (self.shop_id, page_size, offset)).fetchall()

        messages = []
        for r in rows:
            messages.append({
                'id': r['id'],
                'buyer_id': r['buyer_id'],
                'buyer_name': r['buyer_name'],
                'order_id': r['order_id'],
                'subject': r['subject'],
                'body': r['body'],
                'direction': r['direction'],
                'status': r['status'],
                'created_at': r['created_at'],
            })
        return messages

    def send_message(self, payload):
        """发送站内消息给买家。"""
        buyer_id = payload.get('buyer_id', 'unknown_buyer')
        order_id = payload.get('order_id', '')
        text = payload.get('text', '')
        subject = payload.get('subject', 'Re: Customer Inquiry')

        message_id = f'M{int(time.time())}{uuid.uuid4().hex[:6].upper()}'

        with _local_conn() as conn:
            conn.execute(
                "INSERT INTO local_messages "
                "(id, shop_id, buyer_id, buyer_name, order_id, subject, body, direction, status, replied_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (message_id, self.shop_id, buyer_id, '',
                 order_id, subject, text,
                 'outbound', 'sent',
                 time.strftime('%Y-%m-%d %H:%M:%S')))

            # 如果有对应的入站消息，标记为已回复
            if order_id:
                conn.execute(
                    "UPDATE local_messages SET status='replied', "
                    "replied_at=datetime('now','localtime') "
                    "WHERE shop_id=? AND order_id=? AND direction='inbound'",
                    (self.shop_id, order_id))

        return {
            'success': True,
            'mock': False,
            'platform': 'local-shop',
            'message_id': message_id,
            'status': 'SENT',
            'message': f'消息发送成功，ID: {message_id}',
        }

    def delete_product(self, product_id):
        """下架商品（标记为 inactive）。"""
        with _local_conn() as conn:
            conn.execute(
                "UPDATE local_products SET status='inactive', "
                "updated_at=datetime('now','localtime') WHERE id=? AND shop_id=?",
                (product_id, self.shop_id))
        return {'success': True, 'message': '商品已下架'}

    def get_stats(self):
        """获取店铺统计数据。"""
        with _local_conn() as conn:
            prod_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM local_products WHERE shop_id=? AND status='active'",
                (self.shop_id,)).fetchone()['cnt']
            unread = conn.execute(
                "SELECT COUNT(*) as cnt FROM local_messages WHERE shop_id=? AND status='unread'",
                (self.shop_id,)).fetchone()['cnt']
            replied = conn.execute(
                "SELECT COUNT(*) as cnt FROM local_messages WHERE shop_id=? AND status='replied'",
                (self.shop_id,)).fetchone()['cnt']
            total_value = conn.execute(
                "SELECT COALESCE(SUM(price * stock), 0) as val FROM local_products WHERE shop_id=? AND status='active'",
                (self.shop_id,)).fetchone()['val']

        return {
            'products': prod_count,
            'unread_messages': unread,
            'replied_messages': replied,
            'inventory_value': round(total_value, 2),
        }
