"""后端 SQLite 数据访问层（零依赖，使用 Python 标准库 sqlite3）。

持久化三大模块的使用记录：
- copywriter_history  文案生成历史
- compliance_history  合规审查历史
- cs_messages         客服消息

设计要点：
- 预留 merchant_id 字段以支持未来多商家隔离，当前默认 'default'（单租户起步）。
- 所有访问均使用参数化查询，避免 SQL 注入。
- 如需迁移到 PostgreSQL，只需替换 get_conn() 与少量 SQL 语法，业务调用不变。
"""
import os
import sqlite3
from contextlib import contextmanager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 部署时通过 AUXAGENT_DATA_DIR 指向持久化目录，避免更新代码时误删业务数据
DATA_DIR = os.environ.get('AUXAGENT_DATA_DIR') or os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'app.db')

DEFAULT_MERCHANT = 'default'
HISTORY_LIMIT = 50
MESSAGE_LIMIT = 200


def get_conn():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_cursor():
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """幂等建表，应用启动时调用一次。"""
    with db_cursor() as conn:
        conn.executescript('''
        CREATE TABLE IF NOT EXISTS copywriter_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            merchant_id TEXT NOT NULL DEFAULT 'default',
            mode TEXT NOT NULL,
            platform TEXT,
            language TEXT,
            input_text TEXT,
            result_json TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS compliance_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            merchant_id TEXT NOT NULL DEFAULT 'default',
            content TEXT,
            options_json TEXT,
            result_json TEXT,
            images_json TEXT DEFAULT '[]',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS cs_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            merchant_id TEXT NOT NULL DEFAULT 'default',
            customer_name TEXT,
            order_id TEXT DEFAULT '',
            message TEXT,
            message_zh TEXT DEFAULT '',
            platform TEXT,
            category TEXT,
            status TEXT DEFAULT 'pending',
            response TEXT DEFAULT '',
            response_zh TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE INDEX IF NOT EXISTS idx_cw_merchant ON copywriter_history(merchant_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_cp_merchant ON compliance_history(merchant_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_cs_merchant ON cs_messages(merchant_id, created_at);

        -- 客服调用历史记录：记录每次 LLM 调用的请求与响应元信息
        CREATE TABLE IF NOT EXISTS cs_invocation_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            merchant_id TEXT NOT NULL DEFAULT 'default',
            platform TEXT DEFAULT '',
            customer_message TEXT NOT NULL,
            ai_response TEXT DEFAULT '',
            status TEXT DEFAULT 'success',
            latency_ms INTEGER DEFAULT 0,
            model_name TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE INDEX IF NOT EXISTS idx_csilog_merchant ON cs_invocation_log(merchant_id, created_at);

        CREATE TABLE IF NOT EXISTS shops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            merchant_id TEXT NOT NULL DEFAULT 'default',
            platform TEXT NOT NULL,
            name TEXT NOT NULL,
            region TEXT,
            credentials_json TEXT DEFAULT '{}',
            status TEXT DEFAULT 'inactive',
            last_error TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS shop_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            payload_json TEXT DEFAULT '{}',
            result_json TEXT DEFAULT '{}',
            status TEXT DEFAULT 'pending',
            error TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_shop_merchant ON shops(merchant_id, platform, status);
        CREATE INDEX IF NOT EXISTS idx_shop_log_shop ON shop_logs(shop_id, created_at);

        -- 物流单据：生成的货运单据记录与状态跟踪
        CREATE TABLE IF NOT EXISTS logistics_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            merchant_id TEXT NOT NULL DEFAULT 'default',
            doc_type TEXT NOT NULL,
            transport_mode TEXT NOT NULL,
            shipper_info_json TEXT DEFAULT '{}',
            consignee_info_json TEXT DEFAULT '{}',
            items_json TEXT DEFAULT '[]',
            totals_json TEXT DEFAULT '{}',
            status TEXT DEFAULT 'generated',
            tracking_number TEXT DEFAULT '',
            carrier TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS logistics_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            location TEXT DEFAULT '',
            description TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (document_id) REFERENCES logistics_documents(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_logistics_merchant ON logistics_documents(merchant_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_logistics_tracking_doc ON logistics_tracking(document_id, created_at);

        -- 已上架商品管理
        CREATE TABLE IF NOT EXISTS published_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            merchant_id TEXT NOT NULL DEFAULT 'default',
            shop_id INTEGER NOT NULL,
            platform TEXT NOT NULL,
            sku TEXT NOT NULL,
            title TEXT NOT NULL,
            bullet_points_json TEXT DEFAULT '[]',
            description TEXT DEFAULT '',
            price REAL DEFAULT 0,
            stock INTEGER DEFAULT 0,
            product_type TEXT DEFAULT '',
            images_json TEXT DEFAULT '[]',
            listing_status TEXT DEFAULT 'active',
            platform_listing_id TEXT DEFAULT '',
            result_meta_json TEXT DEFAULT '{}',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_listings_shop ON published_listings(shop_id, listing_status);
        CREATE INDEX IF NOT EXISTS idx_listings_merchant ON published_listings(merchant_id, created_at);

        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            merchant_id TEXT NOT NULL DEFAULT 'default',
            category TEXT NOT NULL,
            settings_json TEXT NOT NULL DEFAULT '{}',
            updated_at TEXT DEFAULT (datetime('now','localtime')),
            UNIQUE(merchant_id, category)
        );

        -- RAG 知识库表：存储店铺专属的售后规则、FAQ、商品信息、文案风格等
        CREATE TABLE IF NOT EXISTS cs_knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            merchant_id TEXT NOT NULL DEFAULT 'default',
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'faq',
            embedding TEXT DEFAULT '[]',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE INDEX IF NOT EXISTS idx_kb_merchant ON cs_knowledge_base(merchant_id, category);

        -- 对话记忆表：存储每轮客服问答，用于后续检索历史上下文
        CREATE TABLE IF NOT EXISTS cs_conversation_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            merchant_id TEXT NOT NULL DEFAULT 'default',
            customer_question TEXT NOT NULL,
            ai_response TEXT NOT NULL,
            embedding TEXT DEFAULT '[]',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE INDEX IF NOT EXISTS idx_cmem_merchant ON cs_conversation_memory(merchant_id, created_at);
        ''')

        # ---- 轻量级 schema 迁移：为旧版数据库补齐新增字段 ----
        cols = {r[1] for r in conn.execute("PRAGMA table_info(cs_messages)").fetchall()}
        if 'order_id' not in cols:
            conn.execute("ALTER TABLE cs_messages ADD COLUMN order_id TEXT DEFAULT ''")
        if 'response_zh' not in cols:
            conn.execute("ALTER TABLE cs_messages ADD COLUMN response_zh TEXT DEFAULT ''")
        if 'message_zh' not in cols:
            conn.execute("ALTER TABLE cs_messages ADD COLUMN message_zh TEXT DEFAULT ''")
        if 'buyer_id' not in cols:
            conn.execute("ALTER TABLE cs_messages ADD COLUMN buyer_id TEXT DEFAULT ''")
            # 回填：用 customer_name 作为默认 buyer_id
            conn.execute(
                "UPDATE cs_messages SET buyer_id=customer_name "
                "WHERE buyer_id='' AND customer_name IS NOT NULL AND customer_name<>''")
        if 'manual_response' not in cols:
            conn.execute("ALTER TABLE cs_messages ADD COLUMN manual_response TEXT DEFAULT ''")
        if 'manual_response_translated' not in cols:
            conn.execute("ALTER TABLE cs_messages ADD COLUMN manual_response_translated TEXT DEFAULT ''")

        conv_cols = {r[1] for r in conn.execute("PRAGMA table_info(cs_conversation_memory)").fetchall()}
        if 'buyer_id' not in conv_cols:
            conn.execute("ALTER TABLE cs_conversation_memory ADD COLUMN buyer_id TEXT DEFAULT ''")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_cmem_buyer "
                "ON cs_conversation_memory(merchant_id, buyer_id)")

        inv_cols = {r[1] for r in conn.execute("PRAGMA table_info(cs_invocation_log)").fetchall()}
        if 'buyer_id' not in inv_cols:
            conn.execute("ALTER TABLE cs_invocation_log ADD COLUMN buyer_id TEXT DEFAULT ''")

        # ---- 合规审查历史：兼容旧表，添加 images_json 字段 ----
        comp_cols = {r[1] for r in conn.execute("PRAGMA table_info(compliance_history)").fetchall()}
        if 'images_json' not in comp_cols:
            conn.execute("ALTER TABLE compliance_history ADD COLUMN images_json TEXT DEFAULT '[]'")

        # ---- 买家别名表：解决同一买家换名字被当成新买家的问题 ----
        conn.execute('''
        CREATE TABLE IF NOT EXISTS buyer_aliases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            merchant_id TEXT NOT NULL DEFAULT 'default',
            buyer_id TEXT NOT NULL,
            alias TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            UNIQUE(merchant_id, alias)
        )
        ''')
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_ba_merchant_buyer "
            "ON buyer_aliases(merchant_id, buyer_id)")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_ba_merchant_alias "
            "ON buyer_aliases(merchant_id, alias)")


# ---------------- 文案生成历史 ----------------
def add_copywriter_record(merchant_id, mode, platform, language, input_text, result_json):
    with db_cursor() as conn:
        cur = conn.execute(
            "INSERT INTO copywriter_history "
            "(merchant_id, mode, platform, language, input_text, result_json) "
            "VALUES (?,?,?,?,?,?)",
            (merchant_id, mode, platform, language, input_text, result_json))
        return cur.lastrowid


def list_copywriter_records(merchant_id, limit=HISTORY_LIMIT):
    with db_cursor() as conn:
        rows = conn.execute(
            "SELECT * FROM copywriter_history WHERE merchant_id=? "
            "ORDER BY created_at DESC, id DESC LIMIT ?",
            (merchant_id, limit)).fetchall()
        return [dict(r) for r in rows]


def delete_copywriter_record(merchant_id, rec_id):
    with db_cursor() as conn:
        conn.execute(
            "DELETE FROM copywriter_history WHERE merchant_id=? AND id=?",
            (merchant_id, rec_id))


def clear_copywriter_records(merchant_id):
    with db_cursor() as conn:
        conn.execute(
            "DELETE FROM copywriter_history WHERE merchant_id=?",
            (merchant_id,))


# ---------------- 合规审查历史 ----------------
def add_compliance_record(merchant_id, content, options_json, result_json, images_json='[]'):
    with db_cursor() as conn:
        cur = conn.execute(
            "INSERT INTO compliance_history (merchant_id, content, options_json, result_json, images_json) "
            "VALUES (?,?,?,?,?)",
            (merchant_id, content, options_json, result_json, images_json or '[]'))
        return cur.lastrowid


def list_compliance_records(merchant_id, limit=HISTORY_LIMIT):
    with db_cursor() as conn:
        rows = conn.execute(
            "SELECT id, merchant_id, content, options_json, result_json, images_json, created_at "
            "FROM compliance_history WHERE merchant_id=? "
            "ORDER BY created_at DESC, id DESC LIMIT ?",
            (merchant_id, limit)).fetchall()
        return [dict(r) for r in rows]


def delete_compliance_record(merchant_id, rec_id):
    with db_cursor() as conn:
        conn.execute(
            "DELETE FROM compliance_history WHERE merchant_id=? AND id=?",
            (merchant_id, rec_id))


def clear_compliance_records(merchant_id):
    with db_cursor() as conn:
        conn.execute(
            "DELETE FROM compliance_history WHERE merchant_id=?",
            (merchant_id,))


# ---------------- 客服消息 ----------------
def add_message(merchant_id, customer_name, message, platform, category, order_id='', buyer_id=''):
    with db_cursor() as conn:
        cur = conn.execute(
            "INSERT INTO cs_messages "
            "(merchant_id, customer_name, order_id, message, platform, category, buyer_id) "
            "VALUES (?,?,?,?,?,?,?)",
            (merchant_id, customer_name, order_id, message, platform, category,
             buyer_id or customer_name))
        return cur.lastrowid


def message_exists(merchant_id, buyer_id, message, order_id=''):
    """检查是否已存在相同买家、相同内容、相同订单的消息（用于同步去重）。"""
    with db_cursor() as conn:
        row = conn.execute(
            "SELECT 1 FROM cs_messages "
            "WHERE merchant_id=? AND buyer_id=? AND message=? AND order_id=? "
            "LIMIT 1",
            (merchant_id, buyer_id or '', message or '', order_id or '')
        ).fetchone()
        return row is not None


def get_message(merchant_id, msg_id):
    with db_cursor() as conn:
        row = conn.execute(
            "SELECT * FROM cs_messages WHERE merchant_id=? AND id=?",
            (merchant_id, msg_id)).fetchone()
        return dict(row) if row else None


def list_messages(merchant_id, limit=MESSAGE_LIMIT):
    with db_cursor() as conn:
        rows = conn.execute(
            "SELECT * FROM cs_messages WHERE merchant_id=? "
            "ORDER BY created_at DESC, id DESC LIMIT ?",
            (merchant_id, limit)).fetchall()
        return [dict(r) for r in rows]


def update_message(merchant_id, msg_id, response, response_zh, status, message_zh='', manual_response='', manual_response_translated=''):
    with db_cursor() as conn:
        conn.execute(
            "UPDATE cs_messages "
            "SET response=?, response_zh=?, status=?, message_zh=?, manual_response=?, manual_response_translated=?, updated_at=datetime('now','localtime') "
            "WHERE merchant_id=? AND id=?",
            (response, response_zh, status, message_zh, manual_response, manual_response_translated, merchant_id, msg_id))


def delete_message(merchant_id, msg_id):
    with db_cursor() as conn:
        conn.execute(
            "DELETE FROM cs_messages WHERE merchant_id=? AND id=?",
            (merchant_id, msg_id))


def clear_messages(merchant_id):
    with db_cursor() as conn:
        conn.execute(
            "DELETE FROM cs_messages WHERE merchant_id=?",
            (merchant_id,))


# ---------------- 客服调用历史记录 ----------------


def add_invocation_log(merchant_id, platform, customer_message, ai_response,
                       status='success', latency_ms=0, model_name='', buyer_id=''):
    with db_cursor() as conn:
        cur = conn.execute(
            "INSERT INTO cs_invocation_log "
            "(merchant_id, platform, customer_message, ai_response, "
            "status, latency_ms, model_name, buyer_id) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (merchant_id, platform, customer_message, ai_response,
             status, latency_ms, model_name, buyer_id))
        return cur.lastrowid


def list_invocation_logs(merchant_id, limit=100):
    with db_cursor() as conn:
        rows = conn.execute(
            "SELECT * FROM cs_invocation_log WHERE merchant_id=? "
            "ORDER BY created_at DESC LIMIT ?",
            (merchant_id, limit)).fetchall()
        return [dict(r) for r in rows]


def clear_invocation_logs(merchant_id):
    with db_cursor() as conn:
        conn.execute(
            "DELETE FROM cs_invocation_log WHERE merchant_id=?",
            (merchant_id,))


# ---------------- RAG 知识库 ----------------
def add_knowledge_entry(merchant_id, title, content, category, embedding):
    with db_cursor() as conn:
        cur = conn.execute(
            "INSERT INTO cs_knowledge_base "
            "(merchant_id, title, content, category, embedding) "
            "VALUES (?,?,?,?,?)",
            (merchant_id, title, content, category, embedding))
        return cur.lastrowid


def get_knowledge_entry(merchant_id, entry_id):
    with db_cursor() as conn:
        row = conn.execute(
            "SELECT * FROM cs_knowledge_base WHERE merchant_id=? AND id=?",
            (merchant_id, entry_id)).fetchone()
        return dict(row) if row else None


def list_knowledge_entries(merchant_id, limit=500):
    with db_cursor() as conn:
        rows = conn.execute(
            "SELECT * FROM cs_knowledge_base WHERE merchant_id=? "
            "ORDER BY category, created_at DESC LIMIT ?",
            (merchant_id, limit)).fetchall()
        return [dict(r) for r in rows]


def update_knowledge_entry(merchant_id, entry_id, title, content, category, embedding):
    with db_cursor() as conn:
        conn.execute(
            "UPDATE cs_knowledge_base SET "
            "title=?, content=?, category=?, embedding=?, "
            "updated_at=datetime('now','localtime') "
            "WHERE merchant_id=? AND id=?",
            (title, content, category, embedding, merchant_id, entry_id))


def delete_knowledge_entry(merchant_id, entry_id):
    with db_cursor() as conn:
        conn.execute(
            "DELETE FROM cs_knowledge_base WHERE merchant_id=? AND id=?",
            (merchant_id, entry_id))


# ---------------- 对话记忆 ----------------
def add_conversation_memory(merchant_id, question, response, embedding, buyer_id='', limit=200):
    """添加对话记忆，超出上限自动清理旧记录"""
    with db_cursor() as conn:
        # 先查数量
        count = conn.execute(
            "SELECT COUNT(*) FROM cs_conversation_memory WHERE merchant_id=?",
            (merchant_id,)).fetchone()[0]
        if count >= limit:
            # 删除最旧的超出部分
            excess = count - limit + 1
            oldest = conn.execute(
                "SELECT id FROM cs_conversation_memory WHERE merchant_id=? "
                "ORDER BY created_at ASC LIMIT ?",
                (merchant_id, excess)).fetchall()
            for row in oldest:
                conn.execute(
                    "DELETE FROM cs_conversation_memory WHERE id=?",
                    (row[0],))

        cur = conn.execute(
            "INSERT INTO cs_conversation_memory "
            "(merchant_id, customer_question, ai_response, embedding, buyer_id) "
            "VALUES (?,?,?,?,?)",
            (merchant_id, question, response, embedding, buyer_id))
        return cur.lastrowid


def list_conversation_memory(merchant_id, limit=100):
    with db_cursor() as conn:
        rows = conn.execute(
            "SELECT * FROM cs_conversation_memory WHERE merchant_id=? "
            "ORDER BY created_at DESC LIMIT ?",
            (merchant_id, limit)).fetchall()
        return [dict(r) for r in rows]


def list_conversation_memory_by_buyer(merchant_id, buyer_id, limit=20):
    """查询指定买家的历史对话，用于「重复买家咨询」上下文连贯回复"""
    if not buyer_id:
        return []
    with db_cursor() as conn:
        rows = conn.execute(
            "SELECT * FROM cs_conversation_memory WHERE merchant_id=? AND buyer_id=? "
            "ORDER BY created_at DESC LIMIT ?",
            (merchant_id, buyer_id, limit)).fetchall()
        return [dict(r) for r in rows]


def clear_conversation_memory(merchant_id):
    with db_cursor() as conn:
        conn.execute(
            "DELETE FROM cs_conversation_memory WHERE merchant_id=?",
            (merchant_id,))


# ---------------- 店铺 / 平台 API 对接 ----------------
def add_shop(merchant_id, platform, name, region, credentials_json):
    with db_cursor() as conn:
        cur = conn.execute(
            "INSERT INTO shops (merchant_id, platform, name, region, credentials_json) "
            "VALUES (?,?,?,?,?)",
            (merchant_id, platform, name, region, credentials_json))
        return cur.lastrowid


def list_shops(merchant_id, limit=200):
    with db_cursor() as conn:
        rows = conn.execute(
            "SELECT * FROM shops WHERE merchant_id=? ORDER BY created_at DESC, id DESC LIMIT ?",
            (merchant_id, limit)).fetchall()
        return [dict(r) for r in rows]


def get_shop(merchant_id, shop_id):
    with db_cursor() as conn:
        row = conn.execute(
            "SELECT * FROM shops WHERE merchant_id=? AND id=?",
            (merchant_id, shop_id)).fetchone()
        return dict(row) if row else None


def update_shop(merchant_id, shop_id, platform, name, region, credentials_json, status):
    with db_cursor() as conn:
        conn.execute(
            "UPDATE shops SET platform=?, name=?, region=?, credentials_json=?, status=?, "
            "updated_at=datetime('now','localtime') WHERE merchant_id=? AND id=?",
            (platform, name, region, credentials_json, status, merchant_id, shop_id))


def update_shop_status(merchant_id, shop_id, status, last_error=''):
    with db_cursor() as conn:
        conn.execute(
            "UPDATE shops SET status=?, last_error=?, updated_at=datetime('now','localtime') "
            "WHERE merchant_id=? AND id=?",
            (status, last_error, merchant_id, shop_id))


def delete_shop(merchant_id, shop_id):
    with db_cursor() as conn:
        conn.execute(
            "DELETE FROM shops WHERE merchant_id=? AND id=?",
            (merchant_id, shop_id))


def add_shop_log(shop_id, action, payload_json, result_json, status, error=''):
    with db_cursor() as conn:
        cur = conn.execute(
            "INSERT INTO shop_logs (shop_id, action, payload_json, result_json, status, error) "
            "VALUES (?,?,?,?,?,?)",
            (shop_id, action, payload_json, result_json, status, error))
        return cur.lastrowid


def list_shop_logs(shop_id, limit=50):
    with db_cursor() as conn:
        rows = conn.execute(
            "SELECT * FROM shop_logs WHERE shop_id=? ORDER BY created_at DESC, id DESC LIMIT ?",
            (shop_id, limit)).fetchall()
        return [dict(r) for r in rows]


# ---------------- 物流单据 ----------------
import json as _json


def add_logistics_document(merchant_id, doc_type, transport_mode, shipper_info_json,
                           consignee_info_json, items_json, totals_json,
                           status='generated', tracking_number='', carrier=''):
    with db_cursor() as conn:
        cur = conn.execute(
            "INSERT INTO logistics_documents (merchant_id, doc_type, transport_mode, "
            "shipper_info_json, consignee_info_json, items_json, totals_json, status, "
            "tracking_number, carrier) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (merchant_id, doc_type, transport_mode, shipper_info_json, consignee_info_json,
             items_json, totals_json, status, tracking_number, carrier))
        return cur.lastrowid


def list_logistics_documents(merchant_id, limit=200):
    with db_cursor() as conn:
        rows = conn.execute(
            "SELECT * FROM logistics_documents WHERE merchant_id=? "
            "ORDER BY created_at DESC, id DESC LIMIT ?",
            (merchant_id, limit)).fetchall()
        docs = [dict(r) for r in rows]
        for d in docs:
            d['shipper_info'] = _json.loads(d.pop('shipper_info_json') or '{}')
            d['consignee_info'] = _json.loads(d.pop('consignee_info_json') or '{}')
            d['items'] = _json.loads(d.pop('items_json') or '[]')
            d['totals'] = _json.loads(d.pop('totals_json') or '{}')
        return docs


def get_logistics_document(merchant_id, doc_id):
    with db_cursor() as conn:
        row = conn.execute(
            "SELECT * FROM logistics_documents WHERE merchant_id=? AND id=?",
            (merchant_id, doc_id)).fetchone()
        if not row:
            return None
        doc = dict(row)
        doc['shipper_info'] = _json.loads(doc.pop('shipper_info_json') or '{}')
        doc['consignee_info'] = _json.loads(doc.pop('consignee_info_json') or '{}')
        doc['items'] = _json.loads(doc.pop('items_json') or '[]')
        doc['totals'] = _json.loads(doc.pop('totals_json') or '{}')
        return doc


def update_logistics_document(merchant_id, doc_id, **kwargs):
    allowed = {'doc_type', 'transport_mode', 'status', 'tracking_number', 'carrier',
               'shipper_info_json', 'consignee_info_json', 'items_json', 'totals_json'}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_clause = ', '.join([f"{k}=?" for k in fields.keys()])
    values = list(fields.values()) + [merchant_id, doc_id]
    with db_cursor() as conn:
        conn.execute(
            f"UPDATE logistics_documents SET {set_clause}, "
            f"updated_at=datetime('now','localtime') WHERE merchant_id=? AND id=?",
            values)


def add_logistics_tracking(document_id, status, location='', description=''):
    with db_cursor() as conn:
        cur = conn.execute(
            "INSERT INTO logistics_tracking (document_id, status, location, description) "
            "VALUES (?,?,?,?)",
            (document_id, status, location, description))
        return cur.lastrowid


def list_logistics_tracking(document_id):
    with db_cursor() as conn:
        rows = conn.execute(
            "SELECT * FROM logistics_tracking WHERE document_id=? ORDER BY created_at ASC, id ASC",
            (document_id,)).fetchall()
        return [dict(r) for r in rows]


# ---------------- 已上架/待上架商品管理 ----------------
def add_published_listing(merchant_id, shop_id, platform, sku, title,
                          bullet_points_json='[]', description='', price=0, stock=0,
                          product_type='', images_json='[]',
                          listing_status='active', platform_listing_id='',
                          result_meta_json='{}'):
    with db_cursor() as conn:
        cur = conn.execute(
            "INSERT INTO published_listings (merchant_id, shop_id, platform, sku, title, "
            "bullet_points_json, description, price, stock, product_type, images_json, "
            "listing_status, platform_listing_id, result_meta_json) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (merchant_id, shop_id, platform, sku, title, bullet_points_json,
             description, price, stock, product_type, images_json,
             listing_status, platform_listing_id, result_meta_json))
        return cur.lastrowid


def list_published_listings(merchant_id, shop_id=None, limit=200):
    with db_cursor() as conn:
        if shop_id:
            rows = conn.execute(
                "SELECT * FROM published_listings WHERE merchant_id=? AND shop_id=? "
                "ORDER BY updated_at DESC, id DESC LIMIT ?",
                (merchant_id, shop_id, limit)).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM published_listings WHERE merchant_id=? "
                "ORDER BY updated_at DESC, id DESC LIMIT ?",
                (merchant_id, limit)).fetchall()
        docs = [dict(r) for r in rows]
        for d in docs:
            d['bullet_points'] = _json.loads(d.pop('bullet_points_json') or '[]')
            d['images'] = _json.loads(d.pop('images_json') or '[]')
            d['result_meta'] = _json.loads(d.pop('result_meta_json') or '{}')
        return docs


def get_published_listing(merchant_id, listing_id):
    with db_cursor() as conn:
        row = conn.execute(
            "SELECT * FROM published_listings WHERE merchant_id=? AND id=?",
            (merchant_id, listing_id)).fetchone()
        if not row:
            return None
        doc = dict(row)
        doc['bullet_points'] = _json.loads(doc.pop('bullet_points_json') or '[]')
        doc['images'] = _json.loads(doc.pop('images_json') or '[]')
        doc['result_meta'] = _json.loads(doc.pop('result_meta_json') or '{}')
        return doc


def update_published_listing(merchant_id, listing_id, **kwargs):
    allowed = {'title', 'bullet_points_json', 'description', 'price', 'stock',
               'product_type', 'images_json', 'listing_status', 'platform_listing_id',
               'result_meta_json', 'sku'}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_clause = ', '.join([f"{k}=?" for k in fields])
    values = list(fields.values()) + [merchant_id, listing_id]
    with db_cursor() as conn:
        conn.execute(
            f"UPDATE published_listings SET {set_clause}, "
            f"updated_at=datetime('now','localtime') WHERE merchant_id=? AND id=?",
            values)


def delete_published_listing(merchant_id, listing_id):
    with db_cursor() as conn:
        conn.execute("DELETE FROM published_listings WHERE merchant_id=? AND id=?",
                     (merchant_id, listing_id))


# ---------------- 用户设置持久化 ----------------
def get_settings(merchant_id, category):
    """获取指定分类的设置，返回 dict 或空 dict"""
    with db_cursor() as conn:
        row = conn.execute(
            "SELECT settings_json FROM user_settings WHERE merchant_id=? AND category=?",
            (merchant_id, category)).fetchone()
        if row:
            import json
            return json.loads(row['settings_json'])
        return {}


def save_settings(merchant_id, category, settings_dict):
    """保存/覆盖指定分类的设置"""
    import json
    with db_cursor() as conn:
        conn.execute(
            "INSERT INTO user_settings (merchant_id, category, settings_json, updated_at) "
            "VALUES (?,?,?,datetime('now','localtime')) "
            "ON CONFLICT(merchant_id, category) DO UPDATE SET "
            "settings_json=excluded.settings_json, updated_at=excluded.updated_at",
            (merchant_id, category, json.dumps(settings_dict, ensure_ascii=False)))


# ---------------- 买家别名：解决同一买家换名字的识别问题 ----------------
def resolve_buyer_id(merchant_id, buyer_id, customer_name):
    """
    解析真实的 buyer_id：
    1. 如果 buyer_id 有效且非空，记录 customer_name 为别名
    2. 如果 buyer_id 为空，尝试从别名表查找 customer_name 对应的 buyer_id
    3. 都找不到则返回 customer_name（新买家）
    返回: (resolved_buyer_id, is_known)
    """
    if not customer_name:
        return (buyer_id or '', False)

    with db_cursor() as conn:
        if buyer_id and buyer_id.strip():
            # 记录别名映射
            conn.execute(
                "INSERT OR IGNORE INTO buyer_aliases (merchant_id, buyer_id, alias) "
                "VALUES (?,?,?)",
                (merchant_id, buyer_id.strip(), customer_name.strip())
            )
            return (buyer_id.strip(), True)

        # buyer_id 为空，尝试从别名表查找
        row = conn.execute(
            "SELECT buyer_id FROM buyer_aliases "
            "WHERE merchant_id=? AND alias=?",
            (merchant_id, customer_name.strip())
        ).fetchone()
        if row:
            return (row['buyer_id'], True)

        # 新买家：首次出现，自动注册别名
        effective_id = customer_name.strip()
        conn.execute(
            "INSERT OR IGNORE INTO buyer_aliases (merchant_id, buyer_id, alias) "
            "VALUES (?,?,?)",
            (merchant_id, effective_id, effective_id)
        )
        return (effective_id, False)


def link_buyer_alias(merchant_id, buyer_id, alias):
    """手动将某个名字关联到指定 buyer_id"""
    with db_cursor() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO buyer_aliases (merchant_id, buyer_id, alias) "
            "VALUES (?,?,?)",
            (merchant_id, buyer_id.strip(), alias.strip())
        )


def get_buyer_aliases(merchant_id, buyer_id):
    """获取指定 buyer_id 的所有别名"""
    with db_cursor() as conn:
        rows = conn.execute(
            "SELECT alias FROM buyer_aliases WHERE merchant_id=? AND buyer_id=?",
            (merchant_id, buyer_id)
        ).fetchall()
        return [r['alias'] for r in rows]
