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

## 分析规划流程（必须遵守）

在生成分析步骤前，请按以下流程思考：

### 第零步：判断分析场景
根据数据特征和用户表述，判断属于以下哪种场景，不同场景有专属的分析策略（详见领域知识）：

1. **通用表格数据分析**：CSV/Excel 表格，行=样本，列=变量
   - 最通用的场景，涵盖数据概览、相关性、建模等常规分析
   - 参考「泰坦尼克号案例演练」的分析思路

2. **面料/材料物理指标分析**：数据包含物理测试指标（拉伸强度、摩擦系数等）和主观评分
   - 特点：小样本(20-100)、物理→感官非线性映射、指标共线性
   - 参考「面料分析」知识库，优先用 Spearman 相关而非 Pearson

3. **传感器/信号数据分析**：数据是长时间序列（>1000行），采样频率固定
   - 特点：原始信号不能直接建模，需要先提取时域/频域特征
   - 如果当前引擎不支持特征提取方法，主动告知用户并建议替代方案
   - 参考「传感器分析」知识库

### 第一步：识别用户意图
阅读用户的请求，判断属于哪种意图：
- 数据概览：用户想快速了解数据全貌 → 用 describe + distribution
- 分布探索：用户关心某列的分布形态 → 用 distribution 或 detect_outliers
- 变量关系：用户关心两个变量的关系 → 用 scatter / line / correlation
- 多变量探索：用户想看多个变量的关系 → 用 correlation / pairplot
- 寻找关键因素：用户想知道什么影响目标 → 用 correlation + importance 组合
- 预测建模：用户想训练模型做预测 → 用 clean → feature → model 全流程
- 数据清洗：用户想处理数据质量问题 → 用 dedup / fill_missing / detect_outliers / drop_columns
- 特征构造：用户想创建或转换特征 → 用 scale / encode / variance_filter / correlation_select

### 第二步：选择方法
根据意图和场景选择最合适的原子方法（method）：
- 每个步骤只做一件事，优先用原子方法而非全量流水线
- 用户说"只做相关性"→ method: correlation，不要跑全量 EDA
- 用户说"用随机森林看特征重要性"→ method: importance，不要同时跑 train+residual
- 场景适配：面料数据优先 Spearman；传感器数据先看原始波形再规划

### 第三步：组合步骤
如果用户需求需要多个步骤，按逻辑顺序组合：
- 清洗总是在建模之前
- 先 correlation 扫描再 importance 精排（互补验证）
- 先散点图看形态再相关系数度量强度
- 步骤数控制在 1-6 个

### 第四步：验证计划
生成步骤后检查：
- 用户提到的列名在数据中存在吗？
- 步骤之间有依赖关系吗？（如建模前要处理缺失值）
- 方法选择是否匹配数据类型？（分类列不能做相关性分析）
- 如果用户的请求需要引擎暂不支持的方法（如传感器特征提取），在 explanation 中说明

## 可用分析方法速查

分析步骤类型（type）及可用原子方法（method）：
- clean: dedup(去重) / fill_missing(缺失值填充) / detect_outliers(异常值检测) / drop_columns(删除列)
  默认(不填method): 全量清洗流水线
- eda: correlation(相关性矩阵) / distribution(分布直方图+箱线图) / scatter(散点图) / line(折线图) / pairplot(配对散点矩阵) / describe(统计摘要,无图)
  默认(不填method): 全量EDA流水线
- feature: scale(标准化/归一化) / encode(分类编码) / variance_filter(低方差过滤) / correlation_select(相关性特征选择)
  默认(不填method): 按params子参数执行对应操作
- model: train(训练+评估) / importance(特征重要性) / residual(残差诊断)
  默认(不填method): 全量建模流水线(train+importance+residual)
- report: 报告生成

### 方法参数说明
- fill_missing: strategy 选 mean/median/mode/constant, 数值偏态用median, 分类用mode
- detect_outliers: outlier_method 选 iqr/zscore, threshold 默认 1.5
- correlation: corr_method 选 pearson/spearman, 面料数据推荐 spearman
- scale: scale_method 选 standard/minmax, 树模型不需要标准化, 线性模型需要
- encode: encode_method 选 onehot/label
- train/importance/residual: model_type 选 random_forest/xgboost/linear/ridge/lasso

### 组合模式参考
- 快速体检: describe → distribution
- 找关键因素: correlation → importance
- 两变量关系: scatter(trendline=true) → correlation
- 端到端建模: clean → feature → model
- 数据清洗: drop_columns → fill_missing → detect_outliers

回复格式（严格 JSON）：
{
  "steps": [
    {"type": "clean", "description": "...", "params": {}},
    {"type": "eda", "description": "...", "params": {"columns": [], "method": ""}},
    {"type": "model", "description": "...", "params": {"target": "", "model_type": ""}}
  ],
  "explanation": "用通俗语言向工程师解释这个分析计划"
}"""

    MAX_HISTORY = 20  # 最多保留最近 20 条历史消息（10 轮对话）

    def __init__(self, llm_adapter: LLMAdapter, knowledge_dir: str = "knowledge"):
        self.llm = llm_adapter
        self.knowledge_dir = knowledge_dir
        self.chat_history: list = []

    def set_chat_history(self, history: list) -> None:
        """从保存的状态恢复对话历史"""
        self.chat_history = history or []

    def _build_messages_with_context(self, current_msg: str) -> list:
        """构建带历史上下文的 messages：system + 最近历史 + 当前任务"""
        recent = self.chat_history[-self.MAX_HISTORY:] if self.chat_history else []
        return [
            {"role": "system", "content": self.build_system_prompt()},
            *recent,
            {"role": "user", "content": current_msg},
        ]

    def load_knowledge(self) -> str:
        """加载领域知识"""
        knowledge_parts = []
        for filename in ["indicators.yaml", "templates.yaml",
                           "titanic_methodology.yaml", "fabric_analysis.yaml",
                           "sensor_analysis.yaml"]:
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
        """根据用户输入和数据信息生成分析计划（含上下文）"""
        current_msg = f"""当前数据集信息：
- 行数: {df_info.get('shape', [0, 0])[0]}
- 列数: {df_info.get('shape', [0, 0])[1]}
- 数值列: {df_info.get('numeric_columns', [])}
- 分类型列: {df_info.get('categorical_columns', [])}
- 列名: {df_info.get('columns', [])}

用户的请求: {user_input}

请给出分析计划（JSON 格式）。"""
        messages = self._build_messages_with_context(current_msg)

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

    def _build_explain_messages(self, step, metrics: dict) -> list:
        """构建结果解释的 messages，含上下文（explain_result 和 explain_result_stream 共用）"""
        current_msg = f"""请用汽车工程师能理解的语言解释以下分析结果：

步骤类型: {step.type}
步骤描述: {step.description}
分析结果: {json.dumps(metrics, ensure_ascii=False)}

请用 3-5 句话解释这些数字的含义，以及它们对工程师意味着什么。"""
        return self._build_messages_with_context(current_msg)

    def explain_result(self, step: AnalysisStep, metrics: dict) -> str:
        """用自然语言解释分析结果"""
        messages = self._build_explain_messages(step, metrics)
        explanation = self.llm.chat(messages)
        self.chat_history.append({"role": "assistant", "content": explanation})
        return explanation

    def explain_result_stream(self, step, metrics: dict):
        """流式解释分析结果，逐 chunk yield 文本"""
        messages = self._build_explain_messages(step, metrics)
        full_text = ""
        for chunk in self.llm.chat_stream(messages):
            full_text += chunk
            yield chunk
        self.chat_history.append({"role": "assistant", "content": full_text})

    def summarize_conclusions(self, step_results: list, user_notes: str = ""):
        """汇总所有步骤解读，流式生成综合结论（含上下文）"""
        results_text = ""
        for i, r in enumerate(step_results):
            results_text += f"\n步骤{i+1} ({r['type']}): {r.get('explanation', '无解读')}\n"

        user_part = f"\n工程师补充观点:\n{user_notes}" if user_notes else ""

        current_msg = f"""以下是各分析步骤的结果解读，请汇总成一段 200-300 字的综合分析结论。

分析步骤结果:
{results_text}
{user_part}

请用汽车工程领域的专业语言撰写结论，突出重点发现和工程建议。"""
        messages = self._build_messages_with_context(current_msg)
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
