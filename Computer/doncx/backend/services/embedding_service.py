"""
向量嵌入与 FAISS 检索引擎

使用 sentence-transformers 生成文本向量，FAISS 进行高效语义检索。
模型首次加载会自动下载（约 100MB），之后缓存在本地。

技术选型：
- BAAI/bge-small-zh-v1.5：轻量级中文语义模型（~24MB），对中英文均有基本覆盖
- 如需更强多语言能力，可替换为 paraphrase-multilingual-MiniLM-L12-v2
"""
import os
import json
import numpy as np
from utils.logger import log_error

# 强制 HuggingFace 离线模式，避免在中国网络下反复重试连接 HuggingFace 导致阻塞
# 模型如已缓存则直接加载；无缓存时快速失败，降级为关键词匹配
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

# 延迟导入，避免未安装依赖时启动失败
_sentence_transformers = None
_faiss = None

EMBEDDING_MODEL_NAME = os.environ.get(
    'EMBEDDING_MODEL',
    'BAAI/bge-small-zh-v1.5'
)
VECTOR_DIM = 512  # bge-small-zh-v1.5 输出 512 维
INDEX_PATH = None  # 可选：磁盘持久化 FAISS 索引


def _lazy_import():
    global _sentence_transformers, _faiss
    if _sentence_transformers is None:
        try:
            from sentence_transformers import SentenceTransformer
            _sentence_transformers = SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers 未安装，请执行: pip install sentence-transformers"
            )
    if _faiss is None:
        try:
            import faiss
            _faiss = faiss
        except ImportError:
            raise ImportError(
                "faiss-cpu 未安装，请执行: pip install faiss-cpu"
            )


class EmbeddingService:
    """向量嵌入服务（单例模式，模型只加载一次）"""

    _instance = None
    _model = None
    _ready = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def ensure_ready(self):
        """确保模型已加载（懒加载 + 容错）"""
        if self._ready:
            return True
        try:
            _lazy_import()
            print(f"[EmbeddingService] 正在加载模型: {EMBEDDING_MODEL_NAME} ...")
            self._model = _sentence_transformers(EMBEDDING_MODEL_NAME)
            self._ready = True
            print(f"[EmbeddingService] 模型加载完成，向量维度: {self._model.get_sentence_embedding_dimension()}")
            return True
        except Exception as e:
            log_error('EmbeddingService', f'模型加载失败: {e}')
            print(f"[EmbeddingService] 警告: 模型加载失败，将使用关键词匹配降级方案")
            return False

    def embed(self, texts):
        """
        将文本列表转为向量数组
        返回: numpy array shape (len(texts), dim) 或降级返回 None
        """
        if not self.ensure_ready():
            return None
        if isinstance(texts, str):
            texts = [texts]
        if not texts:
            return np.array([])
        try:
            embeddings = self._model.encode(
                texts,
                normalize_embeddings=True,
                show_progress_bar=False
            )
            return np.array(embeddings, dtype=np.float32)
        except Exception as e:
            log_error('EmbeddingService', f'编码失败: {e}')
            return None

    def embed_single(self, text):
        """编码单条文本，返回 numpy vector；模型不可用时返回 None"""
        result = self.embed(text)
        if result is not None and len(result) > 0:
            return result[0]
        return None

    def service_info(self):
        """返回 embedding 服务状态信息，方便诊断"""
        if not self._ready:
            self.ensure_ready()
        return {
            'ready': self._ready,
            'model_name': EMBEDDING_MODEL_NAME,
            'vector_dim': VECTOR_DIM,
            'dimension': self._model.get_sentence_embedding_dimension() if self._model else 0,
        }

    def build_index(self, vectors):
        """
        构建 FAISS 索引
        参数:
            vectors: numpy array (N, dim)
        返回: faiss.IndexFlatIP（内积搜索，余弦相似度等价于归一化后内积）
        """
        if vectors is None or len(vectors) == 0:
            return None
        _lazy_import()
        dim = vectors.shape[1]
        index = _faiss.IndexFlatIP(dim)  # Inner Product = cosine similarity for normalized vectors
        index.add(vectors)
        return index

    def search(self, query_text, index, id_list, top_k=5):
        """
        搜索最相似的条目
        参数:
            query_text: 查询文本
            index: FAISS 索引
            id_list: 与 index 中向量对应的条目 ID 列表
            top_k: 返回数量
        返回: [(id, score), ...] 按相似度降序排列
        """
        if index is None or not id_list:
            return []
        query_vec = self.embed_single(query_text)
        if query_vec is None:
            return []
        query_vec = query_vec.reshape(1, -1)
        distances, indices = index.search(query_vec, min(top_k, len(id_list)))
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= 0 and idx < len(id_list):
                results.append((id_list[idx], float(dist)))
        return results


# 全局单例
embedding_service = EmbeddingService()
