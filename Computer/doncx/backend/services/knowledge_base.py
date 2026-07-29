"""
店铺专属知识库与对话记忆管理

功能：
1. 知识条目 CRUD（售后规则、FAQ、商品信息、文案风格）
2. 对话记忆存储（记录每轮问答，供后续检索）
3. RAG 检索：根据用户消息，召回相关知识 + 历史对话
"""
import json
import re
import numpy as np
from services.embedding_service import embedding_service
from utils.db import (
    add_knowledge_entry, update_knowledge_entry, delete_knowledge_entry,
    list_knowledge_entries, get_knowledge_entry,
    add_conversation_memory, list_conversation_memory, clear_conversation_memory,
    list_conversation_memory_by_buyer,
    DEFAULT_MERCHANT
)
from utils.logger import log_error

# 知识条目类别（与前端文案一致）
KNOWLEDGE_CATEGORIES = {
    'policy': '售后规则',
    'faq': '常见FAQ',
    'product': '商品信息',
    'style': '文案风格',
}

# 中英双语关键词扩展表：让英文查询也能命中中文知识库，反之亦然
BILINGUAL_KEYWORDS = {
    # 英文 -> 中文
    'return': '退货',
    'returns': '退货',
    'refund': '退款',
    'refunds': '退款',
    'exchange': '换货',
    'shipping': '物流',
    'ship': '发货',
    'delivery': '送货',
    'deliver': '配送',
    'order': '订单',
    'orders': '订单',
    'item': '商品',
    'items': '商品',
    'product': '产品',
    'products': '产品',
    'warranty': '保修',
    'guarantee': '质保',
    'damaged': '损坏',
    'damage': '损坏',
    'broken': '坏了',
    'defective': '缺陷',
    'cancel': '取消',
    'cancellation': '取消',
    'late': '延迟',
    'delayed': '延误',
    'delay': '延误',
    'track': '追踪',
    'tracking': '追踪',
    'package': '包裹',
    'parcel': '包裹',
    'lost': '丢失',
    'missing': '丢失',
    'received': '收到',
    'receive': '收到',
    'wrong': '错误',
    'size': '尺码',
    'color': '颜色',
    'quality': '质量',
    'discount': '折扣',
    'coupon': '优惠券',
    'promotion': '促销',
    'sale': '促销',
    'stock': '库存',
    'price': '价格',
    'payment': '支付',
    'invoice': '发票',
    'customs': '海关',
    'tax': '税费',
    'duties': '关税',
    # 中文 -> 英文（反向）
    '退货': 'return',
    '退款': 'refund',
    '换货': 'exchange',
    '物流': 'shipping',
    '发货': 'ship',
    '送货': 'delivery',
    '配送': 'deliver',
    '订单': 'order',
    '商品': 'item',
    '产品': 'product',
    '保修': 'warranty',
    '质保': 'guarantee',
    '损坏': 'damaged',
    '缺陷': 'defective',
    '取消': 'cancel',
    '延误': 'delayed',
    '延迟': 'delay',
    '追踪': 'tracking',
    '包裹': 'package',
    '丢失': 'lost',
    '收到': 'received',
    '尺码': 'size',
    '颜色': 'color',
    '质量': 'quality',
    '折扣': 'discount',
    '优惠券': 'coupon',
    '促销': 'promotion',
    '库存': 'stock',
    '价格': 'price',
    '支付': 'payment',
}


def _extract_keywords(text):
    """
    从查询文本中提取关键词，支持中文 bigram 和英文单词，
    并通过 BILINGUAL_KEYWORDS 进行中英扩展，使英文查询也能命中中文知识库。
    例如 "Can I return this item after 6 days?" → 包含 "return"、"item"、"退货"、"商品"
    """
    text = text.lower().strip()
    keywords = set()

    # 英文/数字：按空格和标点分词
    en_words = re.findall(r'[a-z0-9]+', text)
    for w in en_words:
        if len(w) > 1:
            keywords.add(w.lower())
        # 保留短英文词，并通过双语表扩展中文等价词
        if len(w) >= 2:
            zh_equivalent = BILINGUAL_KEYWORDS.get(w.lower())
            if zh_equivalent:
                keywords.add(zh_equivalent)

    # 中文：提取纯中文字符串，生成双字 bigram
    chinese_chars = re.sub(r'[^\u4e00-\u9fff]', '', text)
    for i in range(len(chinese_chars) - 1):
        bigram = chinese_chars[i:i + 2]
        keywords.add(bigram)
        # 通过双语表扩展英文等价词
        en_equivalent = BILINGUAL_KEYWORDS.get(bigram)
        if en_equivalent:
            keywords.add(en_equivalent)

    # 也加入单字作为兜底（短词匹配）
    for ch in chinese_chars:
        keywords.add(ch)

    return keywords


class KnowledgeBase:
    """知识库管理服务"""

    def __init__(self, merchant_id=DEFAULT_MERCHANT):
        self.merchant_id = merchant_id
        # 内存缓存
        self._entries_cache = None     # [(id, title, content, category, embedding_str), ...]
        self._index_cache = None       # FAISS index for knowledge entries
        self._id_list_cache = None     # [id, ...] 与 index 行对应

        # 对话记忆缓存
        self._memory_cache = None      # [(id, question, response, embedding_str), ...]
        self._memory_index_cache = None
        self._memory_id_list_cache = None

    # ────────── 知识条目管理 ──────────

    def add_entry(self, title, content, category='faq'):
        """添加知识条目，自动生成 embedding 并持久化"""
        vec = embedding_service.embed_single(f"{title}\n{content}")
        embedding_str = json.dumps(vec.tolist()) if vec is not None else '[]'
        entry_id = add_knowledge_entry(
            self.merchant_id, title, content, category, embedding_str
        )
        self._invalidate_cache()
        return entry_id

    def update_entry(self, entry_id, title=None, content=None, category=None):
        """更新知识条目（部分更新）"""
        existing = get_knowledge_entry(self.merchant_id, entry_id)
        if not existing:
            return False

        new_title = title if title is not None else existing.get('title', '')
        new_content = content if content is not None else existing.get('content', '')
        new_category = category if category is not None else existing.get('category', 'faq')

        # 内容变了就重新生成 embedding
        if title is not None or content is not None:
            vec = embedding_service.embed_single(f"{new_title}\n{new_content}")
            embedding_str = json.dumps(vec.tolist()) if vec is not None else existing.get('embedding', '[]')
        else:
            embedding_str = existing.get('embedding', '[]')

        update_knowledge_entry(
            self.merchant_id, entry_id,
            new_title, new_content, new_category, embedding_str
        )
        self._invalidate_cache()
        return True

    def delete_entry(self, entry_id):
        """删除知识条目"""
        delete_knowledge_entry(self.merchant_id, entry_id)
        self._invalidate_cache()

    def list_entries(self):
        """列出所有知识条目"""
        return list_knowledge_entries(self.merchant_id)

    # ────────── 对话记忆管理 ──────────

    def remember_conversation(self, question, response, buyer_id=''):
        """存储一轮对话到记忆库（标识买家，用于后续「重复买家」上下文检索）"""
        vec = embedding_service.embed_single(question)
        embedding_str = json.dumps(vec.tolist()) if vec is not None else '[]'
        add_conversation_memory(
            self.merchant_id, question, response, embedding_str, buyer_id
        )
        self._memory_cache = None
        self._memory_index_cache = None
        self._memory_id_list_cache = None

    def get_buyer_history(self, buyer_id):
        """获取指定买家的全部历史对话（不依赖向量检索，直接按 buyer_id 查询）"""
        if not buyer_id:
            return []
        rows = list_conversation_memory_by_buyer(self.merchant_id, buyer_id)
        return [{'id': r['id'], 'question': r['customer_question'],
                 'response': r['ai_response'], 'created_at': r.get('created_at', '')}
                for r in rows]

    # ────────── RAG 检索 ──────────

    def _ensure_index(self):
        """确保知识库索引已构建，无效向量的条目也保留在缓存中供关键词兜底"""
        if self._entries_cache is None:
            entries = list_knowledge_entries(self.merchant_id)
            self._entries_cache = []
            vectors = []
            for e in entries:
                eid = e['id']
                emb_str = e.get('embedding', '[]')
                try:
                    vec = json.loads(emb_str) if isinstance(emb_str, str) else emb_str
                    if isinstance(vec, list) and len(vec) > 0:
                        vectors.append(vec)
                        self._entries_cache.append((eid, e['title'], e['content'], e['category'], emb_str))
                    else:
                        # embedding 为空，仍加入缓存供关键词兜底
                        self._entries_cache.append((eid, e['title'], e['content'], e['category'], '[]'))
                except (json.JSONDecodeError, TypeError):
                    # embedding 无效，加入缓存供关键词兜底
                    self._entries_cache.append((eid, e['title'], e['content'], e['category'], '[]'))

            if vectors:
                vec_array = np.array(vectors, dtype=np.float32)
                self._index_cache = embedding_service.build_index(vec_array)
                self._id_list_cache = [item[0] for item in self._entries_cache if item[4] != '[]']
            else:
                self._index_cache = None
                self._id_list_cache = []

    def _ensure_memory_index(self):
        """确保对话记忆索引已构建"""
        if self._memory_cache is None:
            memories = list_conversation_memory(self.merchant_id)
            self._memory_cache = []
            vectors = []
            for m in memories:
                emb_str = m.get('embedding', '[]')
                try:
                    vec = json.loads(emb_str) if isinstance(emb_str, str) else emb_str
                    if vec and len(vec) > 0:
                        vectors.append(vec)
                        self._memory_cache.append((m['id'], m['customer_question'], m['ai_response'], emb_str))
                except (json.JSONDecodeError, TypeError):
                    pass

            if vectors:
                vec_array = np.array(vectors, dtype=np.float32)
                self._memory_index_cache = embedding_service.build_index(vec_array)
                self._memory_id_list_cache = [item[0] for item in self._memory_cache]
            else:
                self._memory_index_cache = None
                self._memory_id_list_cache = []

    def search_knowledge(self, query, top_k=5, buyer_id=''):
        """
        RAG 核心检索：
        1. 直接查询该买家的历史对话（保证上下文属于同一人）
        2. 向量检索知识库中相关条目
        3. 向量检索对话记忆中相似历史问答（可能来自其他客户）
        4. 合并返回，附带相似度分数

        返回: {
            'knowledge': [...],
            'memories': [...],
            'buyer_history': [...]   # 该买家本人的历史对话
        }
        """
        self._ensure_index()
        self._ensure_memory_index()

        result = {'knowledge': [], 'memories': [], 'buyer_history': []}

        # 第 0 步：直接查该买家的历史对话（无需向量检索）
        if buyer_id:
            result['buyer_history'] = self.get_buyer_history(buyer_id)

        # 第 1 步：向量检索知识库

        # 向量检索知识库
        knowledge_results = embedding_service.search(
            query, self._index_cache, self._id_list_cache, top_k=top_k
        ) if self._index_cache is not None else []

        # 构建 id -> entry 映射
        entry_map = {item[0]: item for item in self._entries_cache} if self._entries_cache else {}

        for kid, score in knowledge_results:
            entry = entry_map.get(kid)
            if entry and score > 0.3:  # 相似度阈值
                result['knowledge'].append({
                    'id': entry[0],
                    'title': entry[1],
                    'content': entry[2],
                    'category': entry[3],
                    'category_name': KNOWLEDGE_CATEGORIES.get(entry[3], entry[3]),
                    'score': round(score, 4)
                })

        # 关键词兜底/补充：对所有条目做中英双语关键词匹配，
        # 作为向量检索的补充。当向量模型跨语言召回不足时，仍能命中。
        if self._entries_cache:
            query_keywords = _extract_keywords(query)
            for item in self._entries_cache:
                title = (item[1] or '').lower()
                content = (item[2] or '').lower()
                combined = title + ' ' + content
                # 匹配：任一关键词出现在条目文本中
                if any(kw in combined for kw in query_keywords):
                    already = any(k['id'] == item[0] for k in result['knowledge'])
                    if not already:
                        result['knowledge'].append({
                            'id': item[0],
                            'title': item[1],
                            'content': item[2],
                            'category': item[3],
                            'category_name': KNOWLEDGE_CATEGORIES.get(item[3], item[3]),
                            'score': 0.5  # 关键词匹配默认分
                        })

        # 向量检索对话记忆
        memory_results = embedding_service.search(
            query, self._memory_index_cache, self._memory_id_list_cache, top_k=3
        ) if self._memory_index_cache is not None else []

        memory_map = {item[0]: item for item in self._memory_cache} if self._memory_cache else {}

        for mid, score in memory_results:
            mem = memory_map.get(mid)
            if mem and score > 0.5:  # 对话记忆阈值略高，避免不相关干扰
                result['memories'].append({
                    'id': mem[0],
                    'question': mem[1],
                    'response': mem[2],
                    'score': round(score, 4)
                })

        # 按相似度排序
        result['knowledge'].sort(key=lambda x: x['score'], reverse=True)
        result['memories'].sort(key=lambda x: x['score'], reverse=True)

        return result

    def _invalidate_cache(self):
        """使缓存失效"""
        self._entries_cache = None
        self._index_cache = None
        self._id_list_cache = None

    # ────────── 自动品类归纳 ──────────

    def extract_product_categories(self):
        """
        从现有知识库 + 对话记忆中，用 LLM 提取主营商品品类，
        自动写入 knowledge base 的 product 分类。

        返回: {'categories': [...], 'added_count': int}
        """
        # 收集已有的所有 context
        entries = self.list_entries()
        memories = list_conversation_memory(self.merchant_id, limit=100)

        # 构建分析上下文
        kb_text = ""
        for e in entries:
            kb_text += f"[{e.get('category', '')}] {e.get('title', '')}\n{e.get('content', '')}\n\n"

        mem_text = ""
        for m in memories:
            mem_text += f"客户问：{m.get('customer_question', '')}\n回复：{m.get('ai_response', '')}\n"

        context = f"=== 知识库内容 ===\n{kb_text}\n\n=== 客服对话记录 ===\n{mem_text}"

        # 调用 LLM 提取品类
        from config import Config
        from utils.api_client import APIClient
        client = APIClient()

        prompt = f"""你是一个电商数据分析助手。请分析以下店铺知识和客服对话，提取该店铺主营的商品品类。

分析内容：
{context[:8000]}

请仅输出以下格式的 JSON（不要加任何额外解释或 Markdown 标记）：
{{
  "categories": [
    {{
      "name": "品类名称（如：蓝牙耳机、充电宝、手机壳）",
      "confidence": "high/medium/low",
      "evidence": "判断依据的简要说明"
    }}
  ]
}}

要求：
- 最多提取 5 个主要品类；
- 品类名称要简洁准确；
- confidence 根据出现频率和明确程度判断；
- 仅输出 JSON。"""

        messages = [{'role': 'user', 'content': prompt}]
        response, error = client.call_llm(messages, model=Config.MODEL_NAME)

        if error or not response:
            return {'categories': [], 'added_count': 0, 'error': error or 'LLM 未返回内容'}

        # 解析 LLM 返回
        import json as json_mod
        categories = []
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != -1:
                data = json_mod.loads(response[start:end])
                categories = data.get('categories', [])
        except (json_mod.JSONDecodeError, ValueError):
            pass

        # 写入知识库（去重）
        added = 0
        for cat in categories:
            name = cat.get('name', '').strip()
            if not name:
                continue
            # 检查是否已存在
            existing = list_knowledge_entries(self.merchant_id)
            duplicate = False
            for e in existing:
                if e.get('category') == 'product' and name in (e.get('title', '') or ''):
                    duplicate = True
                    break
            if not duplicate:
                self.add_entry(
                    title=name,
                    content=f"主营品类：{name}。证据：{cat.get('evidence', '从知识库和客服对话中归纳')}",
                    category='product'
                )
                added += 1

        return {'categories': categories, 'added_count': added}
