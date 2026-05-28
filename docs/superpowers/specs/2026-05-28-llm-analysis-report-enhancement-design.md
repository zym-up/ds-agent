# LLM 分析解读 + 报告增强 设计文档

## 背景

当前系统存在两个体验问题：

1. **项目名称不可见**: 项目名仅在 sidebar 小字显示，切换到分析/报告页面后用户容易忘记当前项目
2. **LLM 未参与结果解读**: `AnalysisAgent.explain_result()` 已实现但从未被调用，步骤执行后的原始数据和图表直接展示，工程师需自行分析。报告也只罗列数据，缺乏 LLM 的专业解读

## 设计目标

### 问题 1: 页面显示当前项目

- 5 个页面的 `show()` 中，`st.title()` 后增加 `st.info(f"当前项目: {project_name}")` 蓝色信息框
- 仅当 `session_state` 中存在 `project_name` 时显示

### 问题 2: LLM 流式解读 + 自动汇总结论

**核心流程改动:**

```
用户输入需求 → LLM 生成计划 → 步骤执行 → 计算结果
                                   ↓
                    自动流式调用 explain_result_stream()
                    逐字显示 LLM 解读
                                   ↓
                    结果区: [LLM 解读] + [图表/数据]
                                   ↓
                    用户可追问、可输入补充观点
                                   ↓
                    报告包含: 每步 LLM 解读 + AI 综合结论
```

**三个改动文件:**

| 文件 | 改动 |
|------|------|
| `engine/llm_agent.py` | 新增 `chat_stream()`, `explain_result_stream()`, `summarize_conclusions()` |
| `views/analysis.py` | `execute_step()` 后自动流式解读; 对话支持结果上下文追问 |
| `views/report.py` | 报告纳入 LLM 解读; 新增 AI 自动汇总结论 + 工程师补充输入 |

## 详细设计

### 1. engine/llm_agent.py — LLM 能力扩展

#### 1.1 LLMAdapter.chat_stream(messages) → Generator

```python
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
```

#### 1.2 AnalysisAgent.explain_result_stream(step, metrics) → Generator

与现有 `explain_result()` 逻辑相同，但使用 `chat_stream` 逐 chunk 产出。prompt 要求 LLM 用 3-5 句话向汽车工程师解释指标含义。

#### 1.3 AnalysisAgent.summarize_conclusions(step_results, user_notes="") → Generator

- 收集所有已完成步骤的 LLM 解读文本
- 拼接工程师补充观点
- 流式生成 200-300 字综合结论

### 2. views/analysis.py — 步骤执行后自动解读

#### 2.1 execute_step() 改动

步骤计算完成后:

1. 收集指标 (clean → 缺失值处理数; eda → 统计量; model → R²/MSE/特征重要性)
2. 调用 `st.write_stream(agent.explain_result_stream(step, metrics))` 流式显示解读
3. 解读完成后，完整文本存入 `analysis_state.steps[i]["llm_explanation"]`
4. 图表在解读之后展示

#### 2.2 对话上下文增强

用户发送新分析需求时，将已完成步骤的结果摘要拼入消息上下文，确保 LLM 理解当前分析状态。

### 3. views/report.py — 报告增强

#### 3.1 报告 section 内容

`build_section()` 的 `text` 参数使用 `step["llm_explanation"]` 替代当前的 `"步骤类型: xxx"`。

#### 3.2 AI 自动汇总结论

页面新增:
- "生成 AI 结论" 按钮 → 点击后流式显示 LLM 汇总
- 结论文本框预填 AI 汇总结果，工程师可编辑
- "工程师补充观点" 输入框 → 内容拼入 AI 汇总 prompt

## 边界情况

- LLM API 不可用时: `chat_stream` 异常被 `execute_step()` 的 try/except 捕获，解读文本为空字符串，图表仍正常显示
- 无步骤完成时: "生成 AI 结论" 按钮不可点击，给出提示
- 流式中断: 已显示的文本保留，未完成部分丢弃

## 不在此次范围

- 后续页面 UI 美化（另开设计）
- LLM 对话记忆（已有独立待办）
