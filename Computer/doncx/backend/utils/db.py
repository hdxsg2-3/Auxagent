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
DATA_DIR = os.path.join(BASE_DIR, 'data')
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
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS cs_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            merchant_id TEXT NOT NULL DEFAULT 'default',
            customer_name TEXT,
            message TEXT,
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
        ''')


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
def add_compliance_record(merchant_id, content, options_json, result_json):
    with db_cursor() as conn:
        cur = conn.execute(
            "INSERT INTO compliance_history (merchant_id, content, options_json, result_json) "
            "VALUES (?,?,?,?)",
            (merchant_id, content, options_json, result_json))
        return cur.lastrowid


def list_compliance_records(merchant_id, limit=HISTORY_LIMIT):
    with db_cursor() as conn:
        rows = conn.execute(
            "SELECT * FROM compliance_history WHERE merchant_id=? "
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
def add_message(merchant_id, customer_name, message, platform, category):
    with db_cursor() as conn:
        cur = conn.execute(
            "INSERT INTO cs_messages "
            "(merchant_id, customer_name, message, platform, category) "
            "VALUES (?,?,?,?,?)",
            (merchant_id, customer_name, message, platform, category))
        return cur.lastrowid


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


def update_message(merchant_id, msg_id, response, response_zh, status):
    with db_cursor() as conn:
        conn.execute(
            "UPDATE cs_messages "
            "SET response=?, response_zh=?, status=?, updated_at=datetime('now','localtime') "
            "WHERE merchant_id=? AND id=?",
            (response, response_zh, status, merchant_id, msg_id))


def delete_message(merchant_id, msg_id):
    with db_cursor() as conn:
        conn.execute(
            "DELETE FROM cs_messages WHERE merchant_id=? AND id=?",
            (merchant_id, msg_id))
