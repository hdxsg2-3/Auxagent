import json

from flask import Blueprint, request, jsonify
from services.llm_service import LLMService
from utils.validator import CustomerServiceProcessSchema, validate_request
from utils.logger import log_error
from utils.db import (
    list_messages, add_message, get_message, update_message, delete_message,
    clear_messages, DEFAULT_MERCHANT,
    list_knowledge_entries, add_knowledge_entry, get_knowledge_entry,
    update_knowledge_entry, delete_knowledge_entry,
    list_conversation_memory, clear_conversation_memory,
    list_invocation_logs, clear_invocation_logs,
    resolve_buyer_id, link_buyer_alias, get_buyer_aliases
)

bp = Blueprint('customer_service', __name__)

@bp.route('/process', methods=['POST'])
def process():
    data = request.get_json()
    validation = validate_request(CustomerServiceProcessSchema, data)
    
    if not validation['valid']:
        return jsonify({'success': False, 'errors': validation['errors']}), 400
    
    # 解析真实 buyer_id（同一买家即使换名字也能被识别）
    raw_buyer_id = data.get('buyer_id', '')
    customer_name = data.get('customer_name', '')
    resolved_buyer_id, is_known = resolve_buyer_id(
        _merchant(), raw_buyer_id, customer_name
    )
    
    llm_service = LLMService()
    result = llm_service.process_customer_service(
        data['message'],
        data['platform'],
        _merchant(),
        resolved_buyer_id
    )
    
    if result and 'error' in result:
        return jsonify({'success': False, 'message': result['error']}), 400
    
    if result:
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'message': 'Failed to process customer service'}), 500


def _merchant():
    body = request.get_json(silent=True) or {}
    return body.get('merchant_id') or request.args.get('merchant_id') or DEFAULT_MERCHANT


@bp.route('/messages', methods=['GET'])
def messages_list():
    try:
        records = list_messages(_merchant())
        return jsonify({'success': True, 'data': records})
    except Exception as e:
        log_error('customer_service.messages_list', e)
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/messages', methods=['POST'])
def messages_add():
    data = request.get_json() or {}
    try:
        # 解析真实 buyer_id
        customer_name = data.get('customer_name', '客户')
        resolved, _ = resolve_buyer_id(
            _merchant(), data.get('buyer_id', ''), customer_name
        )
        msg_id = add_message(
            _merchant(),
            customer_name,
            data.get('message', ''),
            data.get('platform', 'amazon'),
            data.get('category', 'general'),
            data.get('order_id', ''),
            resolved
        )
        return jsonify({'success': True, 'data': {'id': msg_id}})
    except Exception as e:
        log_error('customer_service.messages_add', e)
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/messages/<int:msg_id>', methods=['PUT'])
def messages_update(msg_id):
    data = request.get_json() or {}
    try:
        manual_response = data.get('manual_response', '')
        manual_response_translated = data.get('manual_response_translated', '')

        # 如果提交了人工回复且没有带翻译，自动翻译成客户咨询的语言
        if manual_response and not manual_response_translated:
            msg = get_message(_merchant(), msg_id)
            if msg:
                llm_service = LLMService()
                trans_result = llm_service.translate_manual_response(
                    manual_response,
                    msg.get('message', ''),
                    msg.get('platform', 'amazon')
                )
                manual_response_translated = trans_result.get('translated_reply', manual_response)

        update_message(
            _merchant(),
            msg_id,
            data.get('response', ''),
            data.get('response_zh', ''),
            data.get('status', 'auto_replied'),
            data.get('message_zh', ''),
            manual_response,
            manual_response_translated
        )
        return jsonify({
            'success': True,
            'data': {
                'id': msg_id,
                'manual_response': manual_response,
                'manual_response_translated': manual_response_translated
            }
        })
    except Exception as e:
        log_error('customer_service.messages_update', e)
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/messages/<int:msg_id>', methods=['DELETE'])
def messages_delete(msg_id):
    try:
        delete_message(_merchant(), msg_id)
        return jsonify({'success': True, 'data': {'id': msg_id}})
    except Exception as e:
        log_error('customer_service.messages_delete', e)
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/messages', methods=['DELETE'])
def messages_clear():
    try:
        clear_messages(_merchant())
        return jsonify({'success': True})
    except Exception as e:
        log_error('customer_service.messages_clear', e)
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------------- RAG 知识库管理 API ----------------
@bp.route('/knowledge', methods=['GET'])
def knowledge_list():
    """列出所有知识条目"""
    try:
        entries = list_knowledge_entries(_merchant())
        return jsonify({'success': True, 'data': entries})
    except Exception as e:
        log_error('customer_service.knowledge_list', e)
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/knowledge', methods=['POST'])
def knowledge_add():
    """添加知识条目（自动生成向量嵌入，若模型不可用则置空靠关键词兜底）"""
    data = request.get_json() or {}
    title = (data.get('title') or '').strip()
    content = (data.get('content') or '').strip()
    if not title or not content:
        return jsonify({'success': False, 'message': '标题和内容不能为空'}), 400
    try:
        from services.knowledge_base import KnowledgeBase
        kb = KnowledgeBase(_merchant())
        entry_id = kb.add_entry(title, content, data.get('category', 'faq'))
        return jsonify({'success': True, 'data': {'id': entry_id}})
    except Exception as e:
        log_error('customer_service.knowledge_add', e)
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/knowledge/<int:entry_id>', methods=['GET'])
def knowledge_get(entry_id):
    """获取单条知识条目"""
    try:
        entry = get_knowledge_entry(_merchant(), entry_id)
        if not entry:
            return jsonify({'success': False, 'message': '条目不存在'}), 404
        return jsonify({'success': True, 'data': entry})
    except Exception as e:
        log_error('customer_service.knowledge_get', e)
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/knowledge/<int:entry_id>', methods=['PUT'])
def knowledge_update(entry_id):
    """更新知识条目（自动重新生成向量嵌入）"""
    data = request.get_json() or {}
    try:
        existing = get_knowledge_entry(_merchant(), entry_id)
        if not existing:
            return jsonify({'success': False, 'message': '条目不存在'}), 404

        from services.knowledge_base import KnowledgeBase
        kb = KnowledgeBase(_merchant())
        kb.update_entry(
            entry_id,
            title=data.get('title', existing.get('title', '')),
            content=data.get('content', existing.get('content', '')),
            category=data.get('category', existing.get('category', 'faq'))
        )
        return jsonify({'success': True, 'data': {'id': entry_id}})
    except Exception as e:
        log_error('customer_service.knowledge_update', e)
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/knowledge/<int:entry_id>', methods=['DELETE'])
def knowledge_delete(entry_id):
    """删除知识条目"""
    try:
        delete_knowledge_entry(_merchant(), entry_id)
        return jsonify({'success': True, 'data': {'id': entry_id}})
    except Exception as e:
        log_error('customer_service.knowledge_delete', e)
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/knowledge/<int:entry_id>/embed', methods=['POST'])
def knowledge_embed(entry_id):
    """为指定知识条目重新生成 embedding（当 embedding 为空或手动触发时使用）"""
    from services.knowledge_base import KnowledgeBase
    try:
        entry = get_knowledge_entry(_merchant(), entry_id)
        if not entry:
            return jsonify({'success': False, 'message': '条目不存在'}), 404

        kb = KnowledgeBase(_merchant())
        kb.update_entry(
            entry_id,
            title=entry.get('title'),
            content=entry.get('content'),
            category=entry.get('category')
        )
        return jsonify({'success': True, 'data': {'id': entry_id}})
    except Exception as e:
        log_error('customer_service.knowledge_embed', e)
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------------- 诊断接口 ----------------
@bp.route('/rag-status', methods=['GET'])
def rag_status():
    """诊断 RAG 系统状态：embedding 模型 + 知识库索引"""
    from services.embedding_service import embedding_service as es
    from services.knowledge_base import KnowledgeBase
    try:
        emb_info = es.service_info()
        kb = KnowledgeBase(_merchant())
        entries = kb.list_entries()
        valid_entries = 0
        for e in entries:
            emb = e.get('embedding', '[]')
            try:
                vec = json.loads(emb) if isinstance(emb, str) else emb
                if isinstance(vec, list) and len(vec) > 0:
                    valid_entries += 1
            except (json.JSONDecodeError, TypeError):
                pass

        return jsonify({
            'success': True,
            'data': {
                'embedding_model_ready': emb_info['ready'],
                'embedding_model': emb_info['model_name'],
                'vector_dim': emb_info['dimension'],
                'total_entries': len(entries),
                'entries_with_embedding': valid_entries,
                'entries_without_embedding': len(entries) - valid_entries,
                'fallback_active': not emb_info['ready'] or valid_entries == 0
            }
        })
    except Exception as e:
        log_error('customer_service.rag_status', e)
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------------- 对话记忆查询 API ----------------
@bp.route('/memory', methods=['GET'])
def memory_list():
    """列出对话记忆"""
    try:
        memories = list_conversation_memory(_merchant())
        return jsonify({'success': True, 'data': memories})
    except Exception as e:
        log_error('customer_service.memory_list', e)
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/memory', methods=['DELETE'])
def memory_clear():
    """清空对话记忆"""
    try:
        clear_conversation_memory(_merchant())
        return jsonify({'success': True})
    except Exception as e:
        log_error('customer_service.memory_clear', e)
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------------- 调用历史记录 API ----------------


@bp.route('/history', methods=['GET'])
def history_list():
    """列出调用历史记录"""
    try:
        logs = list_invocation_logs(_merchant())
        return jsonify({'success': True, 'data': logs})
    except Exception as e:
        log_error('customer_service.history_list', e)
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/history', methods=['DELETE'])
def history_clear():
    """清空调用历史记录"""
    try:
        clear_invocation_logs(_merchant())
        return jsonify({'success': True})
    except Exception as e:
        log_error('customer_service.history_clear', e)
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------------- 买家别名管理 API ----------------
@bp.route('/buyer/aliases', methods=['GET'])
def buyer_aliases_list():
    """查询某个 buyer_id 的所有别名"""
    buyer_id = request.args.get('buyer_id', '').strip()
    if not buyer_id:
        return jsonify({'success': False, 'message': '请提供 buyer_id'}), 400
    try:
        aliases = get_buyer_aliases(_merchant(), buyer_id)
        return jsonify({'success': True, 'data': {'buyer_id': buyer_id, 'aliases': aliases}})
    except Exception as e:
        log_error('customer_service.buyer_aliases_list', e)
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/buyer/aliases', methods=['POST'])
def buyer_aliases_link():
    """手动关联买家别名（将名字链接到已有 buyer_id）"""
    data = request.get_json() or {}
    buyer_id = (data.get('buyer_id') or '').strip()
    alias = (data.get('alias') or '').strip()
    if not buyer_id or not alias:
        return jsonify({'success': False, 'message': 'buyer_id 和 alias 不能为空'}), 400
    try:
        link_buyer_alias(_merchant(), buyer_id, alias)
        return jsonify({'success': True, 'data': {'buyer_id': buyer_id, 'alias': alias}})
    except Exception as e:
        log_error('customer_service.buyer_aliases_link', e)
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------------- 自动品类归纳 API ----------------
@bp.route('/extract-categories', methods=['POST'])
def extract_categories():
    """
    自动从对话记忆和知识库中提取商品主营品类，写入 knowledge base 的 product 分类。
    用 LLM 分析已有的知识条目 + 对话记忆，提取品类列表并持久化。
    """
    from services.knowledge_base import KnowledgeBase
    try:
        kb = KnowledgeBase(_merchant())
        extracted = kb.extract_product_categories()
        return jsonify({'success': True, 'data': extracted})
    except Exception as e:
        log_error('customer_service.extract_categories', e)
        return jsonify({'success': False, 'message': str(e)}), 500
