# LLM 分析解读 + 报告增强 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 步骤执行后 LLM 自动流式解读结果，报告纳入解读与 AI 综合结论，页面显示当前项目名

**Architecture:** 在 `LLMAdapter` 增加流式接口，`AnalysisAgent` 增加流式解读与结论汇总方法，`analysis.py` 步骤执行后自动调用流式解读，`report.py` 改造为 LLM 解读驱动的内容 + AI 自动结论

**Tech Stack:** Python, Streamlit, OpenAI SDK (stream mode), Plotly

---

## 文件影响

| 文件 | 操作 | 职责 |
|------|------|------|
| `engine/llm_agent.py` | 修改 | 新增 `chat_stream`, `explain_result_stream`, `summarize_conclusions` |
| `views/analysis.py` | 修改 | 步骤执行后流式解读; 对话上下文含结果摘要 |
| `views/report.py` | 修改 | 报告纳入 LLM 解读; AI 自动结论 + 工程师补充 |
| `views/data_upload.py` | 修改 | 显示当前项目名 |
| `views/settings.py` | 修改 | 显示当前项目名 |
| `views/history.py` | 修改 | 显示当前项目名 |

---

### Task 1: LLMAdapter 增加流式对话方法

**Files:**
- Modify: `engine/llm_agent.py`

- [ ] **Step 1: 在 LLMAdapter 类中添加 chat_stream 方法**

在 `test_connection` 方法之后添加:

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

- [ ] **Step 2: 验证 chat_stream 可正常导入**

```bash
cd D:/PythonFile/project1 && python -c "from engine.llm_agent import LLMAdapter; print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add engine/llm_agent.py
git commit -m "feat: add chat_stream method to LLMAdapter for streaming responses"
```

---

### Task 2: AnalysisAgent 增加流式解读方法

**Files:**
- Modify: `engine/llm_agent.py`

- [ ] **Step 1: 在 AnalysisAgent 类中添加 explain_result_stream 方法**

在 `explain_result` 方法之后添加:

```python
def explain_result_stream(self, step: AnalysisStep, metrics: dict):
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
```

- [ ] **Step 2: Commit**

```bash
git add engine/llm_agent.py
git commit -m "feat: add explain_result_stream for streaming analysis interpretation"
```

---

### Task 3: AnalysisAgent 增加结论汇总方法

**Files:**
- Modify: `engine/llm_agent.py`

- [ ] **Step 1: 在 AnalysisAgent 类中添加 summarize_conclusions 方法**

在 `explain_result_stream` 方法之后添加:

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add engine/llm_agent.py
git commit -m "feat: add summarize_conclusions for AI-powered report conclusions"
```

---

### Task 4: analysis.py — 步骤执行后自动流式解读

**Files:**
- Modify: `views/analysis.py`

- [ ] **Step 1: 改造 execute_step 函数，步骤完成后增加 LLM 流式解读**

修改 `execute_step` 函数。在步骤计算完成后（每个 `elif step_type == ...` 分支末尾，设置 status 之前），收集指标并流式显示 LLM 解读。

完整替换 `execute_step` 函数:

```python
def execute_step(step_index: int, step_def: dict, df):
    step_type = step_def["type"]
    params = step_def.get("params", {})
    text = ""
    charts = []
    result_df = df
    metrics_for_llm = {}

    try:
        if step_type == "clean":
            result_df, summary = clean_pipeline(df, **params)
            text = f"### 数据清洗完成\n```json\n{json.dumps(summary, ensure_ascii=False, indent=2)}\n```"
            metrics_for_llm = summary

        elif step_type == "eda":
            numeric_cols = params.get("columns") or df.select_dtypes(include=["number"]).columns.tolist()
            result = eda_pipeline(df, numeric_columns=numeric_cols)
            charts = result["charts"]
            text = f"### 探索性分析\n- 行数: {result['row_count']}\n- 列数: {result['column_count']}"
            metrics_for_llm = {
                "行数": result["row_count"],
                "列数": result["column_count"],
                "统计摘要": {k: str(v) for k, v in result.get("stats_summary", {}).items()},
            }

        elif step_type == "model":
            target = params.get("target", "")
            model_type = params.get("model_type", "linear")
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            if target in numeric_cols:
                numeric_cols.remove(target)
            model_df = df[numeric_cols + [target]].dropna()
            X_train, X_test, y_train, y_test = split_data(model_df, target)
            model, train_info = train_regression(X_train, y_train, model_type)
            metrics = evaluate_regression(model, X_test, y_test)
            _, imp_fig = feature_importance(model, numeric_cols)
            charts.append(imp_fig)
            y_pred = model.predict(X_test)
            res_fig = residual_plot(y_test, y_pred)
            charts.append(res_fig)
            text = f"### 建模结果 ({model_type})\n"
            for k, v in metrics.items():
                text += f"- {k}: {v}\n"
            metrics_for_llm = metrics

        elif step_type == "report":
            text = "报告生成请前往「报告导出」页面。"
            metrics_for_llm = {}

        # --- LLM 流式解读 ---
        explanation_text = ""
        if metrics_for_llm and "agent" in st.session_state:
            from engine.llm_agent import AnalysisStep as AS
            agent_step = AS(
                id=step_index + 1,
                type=step_type,
                description=step_def["description"],
            )
            with st.spinner("AI 正在解读结果..."):
                explanation_text = st.write_stream(
                    st.session_state.agent.explain_result_stream(agent_step, metrics_for_llm)
                )
        # --- 解读结束 ---

        st.session_state.analysis_state["steps"][step_index]["status"] = "done"
        st.session_state.analysis_state["steps"][step_index]["llm_explanation"] = explanation_text
        st.session_state.last_result = {
            "text": text, "charts": charts, "dataframe": result_df.head(50) if result_df is not None else None,
            "llm_explanation": explanation_text,
        }

        if "project_id" in st.session_state:
            pm = ProjectManager()
            pm.save_state(st.session_state.project_id, st.session_state.analysis_state)
            for j, chart in enumerate(charts):
                pm.save_chart(st.session_state.project_id,
                              f"step{step_index+1}_chart{j+1}", chart)

    except Exception as e:
        st.session_state.analysis_state["steps"][step_index]["status"] = "error"
        st.session_state.last_result = {"text": f"执行出错: {str(e)}", "charts": [], "dataframe": None, "llm_explanation": ""}

    st.rerun()
```

- [ ] **Step 2: 在结果区显示 LLM 解读**

修改 `show()` 函数中 center_col 的结果显示区域，在图表之前先显示 LLM 解读:

```python
with center_col:
    st.subheader("📈 结果")

    if "last_result" in st.session_state:
        result = st.session_state.last_result
        if result.get("llm_explanation"):
            with st.container(border=True):
                st.markdown(f"🤖 **AI 解读:** {result['llm_explanation']}")
        if result.get("text"):
            st.markdown(result["text"])
        if result.get("charts"):
            for chart in result["charts"]:
                st.plotly_chart(chart, use_container_width=True)
        if result.get("dataframe") is not None:
            st.dataframe(result["dataframe"], use_container_width=True)
```

- [ ] **Step 3: Commit**

```bash
git add views/analysis.py
git commit -m "feat: auto stream LLM explanation after each analysis step"
```

---

### Task 5: analysis.py — 对话上下文含分析结果摘要

**Files:**
- Modify: `views/analysis.py`

- [ ] **Step 1: 在用户发送消息时，将已完成步骤摘要拼入上下文**

修改 `show()` 函数中 `if user_input:` 块，在调用 `agent.plan_analysis` 之前，构建包含已完成步骤摘要的增强输入:

找到这段代码（约 line 46-71）:

```python
user_input = st.chat_input("描述你的分析需求...")
if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    agent = st.session_state.agent
    plan = agent.plan_analysis(user_input, data_info)
```

替换为:

```python
user_input = st.chat_input("描述你的分析需求...")
if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # 构建增强输入：含已完成步骤摘要
    enhanced_input = user_input
    steps = st.session_state.analysis_state.get("steps", [])
    done_steps = [s for s in steps if s.get("status") == "done"]
    if done_steps:
        context_parts = ["\n\n---\n当前已完成的分析步骤:\n"]
        for i, s in enumerate(done_steps):
            exp = s.get("llm_explanation", "")
            context_parts.append(f"步骤{i+1} ({s['type']}): {s['description']}")
            if exp:
                context_parts.append(f"  解读: {exp[:200]}")
        enhanced_input = user_input + "\n".join(context_parts)

    agent = st.session_state.agent
    plan = agent.plan_analysis(enhanced_input, data_info)
```

- [ ] **Step 2: Commit**

```bash
git add views/analysis.py
git commit -m "feat: include completed step summaries in chat context for follow-up questions"
```

---

### Task 6: report.py — 报告纳入 LLM 解读 + AI 自动结论

**Files:**
- Modify: `views/report.py`

- [ ] **Step 1: 重写 report.py 的 show() 函数**

完整替换 `views/report.py` 内容:

```python
"""报告导出页面"""
import streamlit as st
from engine.reporter import generate_html_report, build_section
from engine.project_manager import ProjectManager


def show():
    st.title("📋 报告导出")
    if "project_name" in st.session_state:
        st.info(f"📊 当前项目: **{st.session_state.project_name}**")

    if "project_id" not in st.session_state:
        st.warning("请先创建分析项目。")
        return

    df = st.session_state.get("df")
    project_name = st.session_state.get("project_name", "未命名项目")
    project_id = st.session_state.get("project_id")

    report_title = st.text_input("报告标题", value=f"{project_name} — 分析报告")

    sections = []
    analysis_state = st.session_state.get("analysis_state", {})
    for step in analysis_state.get("steps", []):
        if step["status"] == "done":
            explanation = step.get("llm_explanation", f"步骤类型: {step['type']}")
            sections.append(build_section(
                title=step["description"],
                text=explanation,
            ))

    if "last_result" in st.session_state and st.session_state.last_result.get("llm_explanation"):
        last_exp = st.session_state.last_result["llm_explanation"]
        already_included = any(
            s.get("llm_explanation") == last_exp
            for s in analysis_state.get("steps", [])
        )
        if not already_included:
            sections.append(build_section(
                title="最新结果解读",
                text=last_exp,
            ))

    # --- AI 自动汇总结论 ---
    if "conclusion_text" not in st.session_state:
        st.session_state.conclusion_text = ""

    st.subheader("🤖 AI 综合结论")

    col_ai, col_user = st.columns([2, 1])
    with col_user:
        user_notes = st.text_area(
            "工程师补充观点",
            placeholder="输入你的分析观点，AI 会结合这些生成结论...",
            height=120,
        )

    with col_ai:
        done_steps = [
            {"type": s["type"], "explanation": s.get("llm_explanation", "")}
            for s in analysis_state.get("steps", [])
            if s["status"] == "done"
        ]
        if st.button("生成 AI 结论", type="primary", disabled=not done_steps):
            if "agent" in st.session_state and done_steps:
                with st.spinner("AI 正在汇总分析结论..."):
                    conclusion_text = st.write_stream(
                        st.session_state.agent.summarize_conclusions(done_steps, user_notes)
                    )
                    st.session_state.conclusion_text = conclusion_text
            else:
                st.warning("请先完成至少一个分析步骤。")

    conclusion = st.text_area(
        "分析结论",
        value=st.session_state.conclusion_text,
        placeholder="点击「生成 AI 结论」自动生成，或手动填写...",
        height=150,
    )
    # --- 结论区域结束 ---

    if st.button("生成报告", type="primary"):
        rows, cols = df.shape if df is not None else (0, 0)
        html = generate_html_report(
            title=report_title,
            sections=sections,
            conclusion=conclusion or "分析完成",
            data_source=project_name,
            rows=rows,
            cols=cols,
        )

        pm = ProjectManager()
        report_path = pm.save_report(project_id, html)
        st.success(f"报告已生成: {report_path}")

        with st.expander("报告预览"):
            st.components.v1.html(html, height=600, scrolling=True)

        with open(report_path, "r", encoding="utf-8") as f:
            st.download_button(
                "下载报告 (HTML)",
                data=f.read(),
                file_name=f"{project_name}_report.html",
                mime="text/html",
            )
```

- [ ] **Step 2: Commit**

```bash
git add views/report.py
git commit -m "feat: enhanced report with LLM explanations and AI auto-conclusion"
```

---

### Task 7: 各页面添加当前项目名显示

**Files:**
- Modify: `views/analysis.py`
- Modify: `views/data_upload.py`
- Modify: `views/settings.py`
- Modify: `views/history.py`

- [ ] **Step 1: analysis.py — 在 st.title 后添加项目名显示**

在 `show()` 函数的 `st.title("🔬 分析对话")` 之后添加:

```python
if "project_name" in st.session_state:
    st.info(f"📊 当前项目: **{st.session_state.project_name}**")
```

- [ ] **Step 2: data_upload.py — 同样的修改**

在 `st.title("📂 数据上传")` 之后添加相同代码。

- [ ] **Step 3: settings.py — 同样的修改**

在 `st.title("⚙ 设置")` 之后添加相同代码。

- [ ] **Step 4: history.py — 同样的修改**

在 `st.title("📁 历史项目")` 之后添加相同代码。

- [ ] **Step 5: Commit**

```bash
git add views/analysis.py views/data_upload.py views/settings.py views/history.py
git commit -m "feat: show current project name on all pages"
```
