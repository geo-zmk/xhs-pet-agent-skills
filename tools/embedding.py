"""
embedding.py — 文本向量化与语义去重工具

使用 BGE-M3 或 SentenceTransformers 进行文本 Embedding，
结合 Chroma 向量数据库实现语义去重。

使用方式:
    from tools.embedding import ContentDeduplicator
    dedup = ContentDeduplicator()
    result = await dedup.check_duplicate("新选题", history_notes)
"""

import json
import hashlib
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field, asdict


# ============================================================
# 数据模型
# ============================================================

@dataclass
class DedupResult:
    topic: str = ""
    duplicate_score: float = 0.0
    is_duplicate: bool = False
    similar_notes: list = field(default_factory=list)
    suggestion: str = ""


@dataclass
class ContentRecord:
    note_id: str = ""
    title: str = ""
    content: str = ""
    category: str = ""
    publish_date: str = ""
    tags: list = field(default_factory=list)
    embedding: list = field(default_factory=list)


# ============================================================
# 语义去重器
# ============================================================

class ContentDeduplicator:
    """
    内容去重器

    支持两种模式:
    1. 关键词快速去重（无需模型）
    2. 语义去重（需要嵌入模型）

    首次使用前请安装依赖:
    pip install sentence-transformers chromadb
    """

    def __init__(self, use_semantic: bool = False):
        self.use_semantic = use_semantic
        self.model = None
        self.embedding_dim = 768

        if use_semantic:
            self._init_model()

    def _init_model(self):
        """初始化嵌入模型"""
        try:
            from sentence_transformers import SentenceTransformer
            # 使用轻量模型，BGE-M3 较大可替换为 all-MiniLM
            self.model = SentenceTransformer("BAAI/bge-small-zh-v1.5")
            self.embedding_dim = 384
        except ImportError:
            print(
                "警告: sentence-transformers 未安装，降级为关键词去重。"
                "安装: pip install sentence-transformers"
            )
            self.use_semantic = False

    def _keyword_similarity(self, text1: str, text2: str) -> float:
        """关键词相似度计算（快速模式）"""
        # 提取关键词
        def extract_keywords(text: str) -> set:
            # 使用简单分词（按常见分隔符）
            words = set()
            for part in text.split():
                # 过滤常见停用词
                stop_words = {
                    "的", "了", "在", "是", "我", "有", "和", "就",
                    "不", "人", "都", "一", "一个", "上", "也", "很",
                    "到", "说", "要", "去", "你", "会", "着", "没有",
                    "看", "好", "自己", "这", "他", "她", "它", "们"
                }
                if part not in stop_words and len(part) > 1:
                    words.add(part)
            return words

        keywords1 = extract_keywords(text1)
        keywords2 = extract_keywords(text2)

        if not keywords1 or not keywords2:
            return 0.0

        intersection = keywords1 & keywords2
        union = keywords1 | keywords2

        return len(intersection) / len(union) if union else 0.0

    def _semantic_similarity(self, text1: str, text2: str) -> float:
        """语义相似度计算"""
        if not self.model:
            return self._keyword_similarity(text1, text2)

        try:
            emb1 = self.model.encode(text1)
            emb2 = self.model.encode(text2)

            # 余弦相似度
            import numpy as np
            dot_product = np.dot(emb1, emb2)
            norm = np.linalg.norm(emb1) * np.linalg.norm(emb2)
            return float(dot_product / norm) if norm > 0 else 0.0

        except Exception as e:
            print(f"语义相似度计算失败: {e}")
            return self._keyword_similarity(text1, text2)

    def check_duplicate(
        self,
        topic: str,
        history_notes: List[dict],
        threshold: float = 0.70
    ) -> DedupResult:
        """
        检查新选题是否与历史内容重复

        Args:
            topic: 新选题文本
            history_notes: 历史笔记列表
            threshold: 重复阈值（0-1）

        Returns:
            DedupResult 去重结果
        """
        result = DedupResult(topic=topic)

        if not history_notes:
            result.duplicate_score = 0.0
            result.is_duplicate = False
            result.suggestion = "历史内容为空，无重复风险"
            return result

        max_similarity = 0.0
        similar_items = []

        for note in history_notes:
            # 组合标题和内容
            note_text = (
                note.get("title", "")
                + " " + note.get("content", "")
                + " " + " ".join(note.get("tags", []))
            )

            if self.use_semantic:
                similarity = self._semantic_similarity(topic, note_text)
            else:
                similarity = self._keyword_similarity(topic, note_text)

            if similarity > threshold * 0.5:  # 记录低阈值也记录
                similar_items.append({
                    "note_id": note.get("note_id", ""),
                    "title": note.get("title", ""),
                    "similarity": round(similarity, 4),
                    "publish_date": note.get("publish_time", note.get("publish_date", ""))
                })

            max_similarity = max(max_similarity, similarity)

        result.duplicate_score = round(max_similarity, 4)
        result.is_duplicate = max_similarity > threshold

        # 排序取最相似的
        similar_items.sort(key=lambda x: x["similarity"], reverse=True)
        result.similar_notes = similar_items[:3]

        # 生成建议
        if result.is_duplicate:
            if max_similarity > 0.85:
                result.suggestion = "高度重复，建议更换选题或更换完全不同角度"
            else:
                result.suggestion = (
                    f"存在相似历史内容（相似度{max_similarity:.0%}），"
                    "建议更换切入角度或增加差异化内容"
                )

            if similar_items:
                top = similar_items[0]
                result.suggestion += (
                    f"。最相似笔记: 「{top['title']}」"
                    f"(发表于{top.get('publish_date', '未知')})"
                )
        else:
            result.suggestion = "无重复风险，可以创作"

        return result

    def batch_check(
        self,
        topics: List[str],
        history_notes: List[dict],
        threshold: float = 0.70
    ) -> List[DedupResult]:
        """批量去重检测"""
        results = []
        for topic in topics:
            result = self.check_duplicate(topic, history_notes, threshold)
            results.append(result)
        return results

    def save_content_history(self, notes: List[dict], filepath: str):
        """保存内容到历史库"""
        records = []
        for note in notes:
            record = ContentRecord(
                note_id=note.get("note_id", ""),
                title=note.get("title", ""),
                content=note.get("content", ""),
                category=note.get("category", ""),
                publish_date=note.get("publish_time", ""),
                tags=note.get("tags", []),
            )

            if self.model:
                text = record.title + " " + record.content[:500]
                try:
                    record.embedding = self.model.encode(text).tolist()
                except Exception:
                    pass

            records.append(asdict(record))

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

    def load_content_history(self, filepath: str) -> List[dict]:
        """从历史库加载内容"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []


# ============================================================
# Chroma 向量数据库集成
# ============================================================

class VectorStore:
    """
    向量数据库封装

    支持 Chroma 和简单的 JSON 文件两种后端。
    """

    def __init__(self, persist_dir: str = "memory/vector_store"):
        self.persist_dir = persist_dir
        self.collection = None
        self._init_chroma()

    def _init_chroma(self):
        """初始化 Chroma"""
        try:
            import chromadb
            self.client = chromadb.PersistentClient(path=self.persist_dir)
            self.collection = self.client.get_or_create_collection(
                name="cat_notes",
                metadata={"hnsw:space": "cosine"}
            )
        except ImportError:
            print("chromadb 未安装，向量数据库不可用")
            self.collection = None

    def add_notes(self, notes: List[dict], embeddings: List[list]):
        """添加笔记到向量库"""
        if not self.collection:
            return

        ids = [note.get("note_id", hashlib.md5(
            note.get("title", "").encode()
        ).hexdigest()) for note in notes]

        metadatas = [
            {
                "title": note.get("title", ""),
                "category": note.get("category", ""),
                "publish_time": note.get("publish_time", ""),
                "likes": note.get("likes", 0),
            }
            for note in notes
        ]

        documents = [
            note.get("title", "") + " " + note.get("content", "")
            for note in notes
        ]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )

    def search_similar(
        self, query_embedding: list, top_k: int = 5
    ) -> List[dict]:
        """搜索相似内容"""
        if not self.collection:
            return []

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        formatted = []
        if results["ids"]:
            for i in range(len(results["ids"][0])):
                formatted.append({
                    "id": results["ids"][0][i],
                    "similarity": 1 - results["distances"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "document": results["documents"][0][i],
                })

        return formatted


# ============================================================
# 快捷使用
# ============================================================

def main():
    """示例：使用去重器"""
    dedup = ContentDeduplicator(use_semantic=False)

    # 加载历史内容
    history = dedup.load_content_history("memory/content_history.json")

    # 检查新选题
    topic = "银虎斑美短文身基因解析｜一篇看懂所有花纹的由来"
    result = dedup.check_duplicate(topic, history)

    print(f"选题: {topic}")
    print(f"重复分数: {result.duplicate_score}")
    print(f"是否重复: {'是' if result.is_duplicate else '否'}")
    print(f"建议: {result.suggestion}")

    if result.similar_notes:
        print("相似内容:")
        for n in result.similar_notes:
            print(f"  - {n['title']} (相似度: {n['similarity']:.0%})")


if __name__ == "__main__":
    main()
