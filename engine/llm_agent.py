"""LLM Agent 编排模块"""
import json
import yaml
import os
from dataclasses import dataclass, field
from typing import Optional
from openai import OpenAI
from engine.config import LLMConfig


@dataclass
class AnalysisStep:
    id: int
    type: str
    description: str
    params: dict = field(default_factory=dict)
    status: str = "pending"


@dataclass
class AnalysisPlan:
    steps: list = field(default_factory=list)
    raw_response: str = ""


class LLMAdapter:
    """兼容 OpenAI API 格式的通用适配器"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = OpenAI(base_url=config.base_url, api_key=config.api_key)

    def chat(self, messages: list) -> str:
        """发送对话请求"""
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        return response.choices[0].message.content

    def test_connection(self) -> tuple:
        """测试 API 连接"""
        try:
            resp = self.chat([{"role": "user", "content": "你好，请回复'连接成功'"}])
            return True, resp
        except Exception as e:
            return False, str(e)

    def chat_stream(self, messages: list):
        """流式对话，逐 chunk yield 文本"""
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            stream=True,
        )
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class AnalysisAgent:
    """数据分析 Agent — 负责理解需求、规划步骤、解释结果"""

    SYSTEM_PROMPT = """你是一个汽车工程数据分析助手。你的用户是汽车研发工程师。

你的职责：
1. 理解工程师的数据分析需求
2. 将需求拆解为具体的分析步骤
3. 用通俗语言解释分析结果

分析步骤类型（type）取值：
- clean: 数据清洗（缺失值、异常值、去重）
- eda: 探索性分析（描述统计、分布图、相关性分析）
- feature: 特征工程（标准化、编码、特征选择）
- model: 建模（回归、分类、聚类）
- report: 报告生成

回复格式（严格 JSON）：
{
  "steps": [
    {"type": "clean", "description": "...", "params": {}},
    {"type": "eda", "description": "...", "params": {"columns": [], "method": ""}},
    {"type": "model", "description": "...", "params": {"target": "", "model_type": ""}}
  ],
  "explanation": "用通俗语言向工程师解释这个分析计划"
}"""

    def __init__(self, llm_adapter: LLMAdapter, knowledge_dir: str = "knowledge"):
        self.llm = llm_adapter
        self.knowledge_dir = knowledge_dir
        self.chat_history: list = []

    def load_knowledge(self) -> str:
        """加载领域知识"""
        knowledge_parts = []
        for filename in ["indicators.yaml", "templates.yaml"]:
            path = os.path.join(self.knowledge_dir, filename)
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    content = yaml.safe_load(f)
                    knowledge_parts.append(yaml.dump(content, allow_unicode=True))
        return "\n".join(knowledge_parts)

    def build_system_prompt(self) -> str:
        """构建包含领域知识的 system prompt"""
        knowledge = self.load_knowledge()
        if knowledge:
            return self.SYSTEM_PROMPT + f"\n\n## 领域知识\n{knowledge}"
        return self.SYSTEM_PROMPT

    def plan_analysis(self, user_input: str, df_info: dict) -> AnalysisPlan:
        """根据用户输入和数据信息生成分析计划"""
        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {"role": "user", "content": f"""当前数据集信息：
- 行数: {df_info.get('shape', [0, 0])[0]}
- 列数: {df_info.get('shape', [0, 0])[1]}
- 数值列: {df_info.get('numeric_columns', [])}
- 分类型列: {df_info.get('categorical_columns', [])}
- 列名: {df_info.get('columns', [])}

用户的请求: {user_input}

请给出分析计划（JSON 格式）。"""},
        ]

        response = self.llm.chat(messages)
        self.chat_history.append({"role": "user", "content": user_input})
        self.chat_history.append({"role": "assistant", "content": response})

        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            else:
                json_str = response

            data = json.loads(json_str.strip())
            steps = [
                AnalysisStep(id=i + 1, **s)
                for i, s in enumerate(data.get("steps", []))
            ]
            return AnalysisPlan(steps=steps, raw_response=data.get("explanation", response))
        except (json.JSONDecodeError, KeyError):
            return AnalysisPlan(steps=[], raw_response=response)

    def explain_result(self, step: AnalysisStep, metrics: dict) -> str:
        """用自然语言解释分析结果"""
        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {"role": "user", "content": f"""请用汽车工程师能理解的语言解释以下分析结果：

步骤类型: {step.type}
步骤描述: {step.description}
分析结果: {json.dumps(metrics, ensure_ascii=False)}

请用 3-5 句话解释这些数字的含义，以及它们对工程师意味着什么。"""},
        ]
        explanation = self.llm.chat(messages)
        self.chat_history.append({"role": "assistant", "content": explanation})
        return explanation

    def explain_result_stream(self, step, metrics: dict):
        """流式解释分析结果，逐 chunk yield 文本"""
        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {"role": "user", "content": f"""请用汽车工程师能理解的语言解释以下分析结果：

步骤类型: {step.type}
步骤描述: {step.description}
分析结果: {json.dumps(metrics, ensure_ascii=False)}

请用 3-5 句话解释这些数字的含义，以及它们对工程师意味着什么。"""},
        ]
        full_text = ""
        for chunk in self.llm.chat_stream(messages):
            full_text += chunk
            yield chunk
        self.chat_history.append({"role": "assistant", "content": full_text})

    def summarize_conclusions(self, step_results: list, user_notes: str = ""):
        """汇总所有步骤解读，流式生成综合结论"""
        results_text = ""
        for i, r in enumerate(step_results):
            results_text += f"\n步骤{i+1} ({r['type']}): {r.get('explanation', '无解读')}\n"

        user_part = f"\n工程师补充观点:\n{user_notes}" if user_notes else ""

        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {"role": "user", "content": f"""以下是各分析步骤的结果解读，请汇总成一段 200-300 字的综合分析结论。

分析步骤结果:
{results_text}
{user_part}

请用汽车工程领域的专业语言撰写结论，突出重点发现和工程建议。"""},
        ]
        full_text = ""
        for chunk in self.llm.chat_stream(messages):
            full_text += chunk
            yield chunk
        self.chat_history.append({"role": "assistant", "content": full_text})

    def suggest_name(self, context: str) -> str:
        """根据分析内容建议项目名称"""
        messages = [
            {"role": "user", "content": f"请为以下数据分析项目起一个简短的中文名称（8个字以内）:\n{context}"}
        ]
        return self.llm.chat(messages).strip().strip('"').strip("'")
