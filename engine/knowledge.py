"""领域知识库管理模块"""
import os
import yaml
from typing import Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class KnowledgeBase:
    """轻量领域知识库 — YAML + TF-IDF 检索"""

    def __init__(self, knowledge_dir: str = "knowledge"):
        self.knowledge_dir = knowledge_dir
        self._indicators: dict = {}
        self._templates: dict = {}
        self._documents: list = []
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._doc_vectors = None
        self.load()

    def load(self) -> None:
        """加载所有知识库文件"""
        indicators_path = os.path.join(self.knowledge_dir, "indicators.yaml")
        if os.path.exists(indicators_path):
            with open(indicators_path, "r", encoding="utf-8") as f:
                self._indicators = yaml.safe_load(f) or {}

        templates_path = os.path.join(self.knowledge_dir, "templates.yaml")
        if os.path.exists(templates_path):
            with open(templates_path, "r", encoding="utf-8") as f:
                self._templates = yaml.safe_load(f) or {}

        ref_dir = os.path.join(self.knowledge_dir, "references")
        if os.path.exists(ref_dir):
            self._documents = []
            texts = []
            for filename in os.listdir(ref_dir):
                if filename.endswith((".txt", ".md")):
                    path = os.path.join(ref_dir, filename)
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    chunks = [c.strip() for c in content.split("\n\n") if c.strip()]
                    for chunk in chunks:
                        if len(chunk) > 20:
                            self._documents.append({"source": filename, "content": chunk})
                            texts.append(chunk)

            if texts:
                self._vectorizer = TfidfVectorizer(max_features=500)
                self._doc_vectors = self._vectorizer.fit_transform(texts)

    def get_indicator_info(self, name: str) -> Optional[dict]:
        """查询指标信息"""
        return self._indicators.get(name)

    def get_template(self, name: str) -> Optional[dict]:
        """查询分析模板"""
        return self._templates.get(name)

    def search_indicators(self, keyword: str) -> list:
        """关键词搜索指标"""
        results = []
        for name, info in self._indicators.items():
            if keyword in name or keyword in info.get("desc", ""):
                results.append({"name": name, **info})
        return results

    def search_documents(self, query: str, top_k: int = 5) -> list:
        """TF-IDF 检索参考文档"""
        if self._vectorizer is None:
            return []
        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._doc_vectors)[0]
        top_indices = np.argsort(scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            if scores[idx] > 0.05:
                results.append({
                    **self._documents[idx],
                    "score": float(scores[idx]),
                })
        return results

    def list_indicators(self) -> list:
        """列出所有指标名称"""
        return list(self._indicators.keys())

    def list_templates(self) -> list:
        """列出所有模板名称"""
        return list(self._templates.keys())

    def get_context_for_llm(self, query: str = "") -> str:
        """生成注入 LLM prompt 的知识上下文"""
        parts = []

        if self._indicators:
            parts.append("## 领域指标知识\n")
            for name, info in self._indicators.items():
                parts.append(f"- {name}: {info.get('desc', '')} (单位: {info.get('unit', 'N/A')})")

        if self._templates:
            parts.append("\n## 分析模板\n")
            for name, tmpl in self._templates.items():
                parts.append(f"- {name}: {'→'.join(tmpl.get('steps', []))}")

        if query:
            docs = self.search_documents(query)
            if docs:
                parts.append("\n## 相关参考文档\n")
                for doc in docs[:3]:
                    parts.append(doc["content"])

        return "\n".join(parts)
