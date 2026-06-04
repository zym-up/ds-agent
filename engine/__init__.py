"""
数据科学家 Agent — 共享分析引擎

提供统一接口的数据处理模块:
- data_loader: 数据加载与解析
- data_cleaner: 数据清洗
- eda: 探索性数据分析
- feature_engineer: 特征工程
- modeler: 模型训练与评估
- reporter: 报告生成
- llm_agent: LLM 编排
- sandbox: 安全代码执行
"""

import math

__version__ = "0.1.0"


def sanitize_json(obj):
    """递归替换 NaN/Infinity 为 None，确保 JSON 兼容"""
    if isinstance(obj, dict):
        return {k: sanitize_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize_json(v) for v in obj]
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
    return obj
