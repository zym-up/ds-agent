"""project_manager 模块测试 — 重点验证 Plotly Figure 序列化修复"""
import json
import os
import tempfile
import pytest
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
from engine.project_manager import ProjectManager


@pytest.fixture
def pm():
    """创建临时目录的 ProjectManager，测试完自动清理"""
    tmp_dir = tempfile.mkdtemp(prefix="pm_test_")
    manager = ProjectManager(projects_dir=tmp_dir)
    yield manager
    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)


class TestCreateProject:
    def test_create_minimal(self, pm):
        pid = pm.create_project("测试项目")
        assert len(pid) == 12  # uuid hex 前12位
        assert os.path.exists(pm.projects_dir / pid / "meta.json")

    def test_create_with_csv(self, pm, sample_df):
        """用 CSV 数据文件创建项目"""
        pid = pm.create_project("带数据项目")
        # 手动写入数据文件
        csv_path = pm.projects_dir / pid / "data" / "original.csv"
        sample_df.to_csv(csv_path, index=False)

        projects = pm.list_projects()
        assert any(p["id"] == pid for p in projects)


class TestListProjects:
    def test_empty(self, pm):
        assert pm.list_projects() == []

    def test_order_by_created(self, pm):
        pm.create_project("A项目")
        pm.create_project("B项目")
        projects = pm.list_projects()
        assert len(projects) == 2
        # 按创建时间倒序
        assert projects[0]["name"] == "B项目"


class TestStateSerialization:
    """验证 state.json 中 Plotly Figure 的正确序列化/反序列化"""

    def test_roundtrip_preserves_figures(self, pm):
        """核心测试：Figure → 保存 → 加载 → 还是 Figure（rounds 格式）"""
        pid = pm.create_project("图表测试")

        # 构造包含 Plotly Figure 的状态（rounds 格式）
        fig1 = px.scatter(x=[1, 2, 3], y=[4, 5, 6], title="测试散点图")
        fig2 = px.line(x=[1, 2, 3], y=[7, 8, 9], title="测试折线图")

        state = {
            "rounds": [{
                "id": 1,
                "user_input": "测试",
                "plan_explanation": "",
                "steps": [
                    {
                        "id": 1,
                        "type": "eda",
                        "description": "探索性分析",
                        "status": "done",
                        "last_charts": [fig1, fig2],
                        "last_text": "分析完成",
                        "llm_explanation": "这是AI解读",
                    },
                ],
                "current_step": 0,
                "created_at": "",
            }],
            "current_round": 0,
        }

        # 保存
        pm.save_state(pid, state)

        # 检查 JSON 文件内容 — 里面应该是合法的 Plotly JSON 而不是 "Figure(...)"
        state_path = pm.projects_dir / pid / "state.json"
        with open(state_path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        chart_data = raw["rounds"][0]["steps"][0]["last_charts"][0]
        # 序列化后应该是 JSON 字符串（以 "{" 开头）
        assert isinstance(chart_data, str)
        assert chart_data.startswith("{")
        assert '"data"' in chart_data  # Plotly JSON 的标准字段

        # 加载
        loaded = pm.load_project(pid)
        loaded_charts = loaded["state"]["rounds"][0]["steps"][0]["last_charts"]

        # 应该还原为 Figure 对象
        assert len(loaded_charts) == 2
        for chart in loaded_charts:
            assert isinstance(chart, go.Figure)

    def test_state_without_charts(self, pm):
        """没有图表的步骤也能正常保存加载（rounds 格式）"""
        pid = pm.create_project("无图表项目")

        state = {
            "rounds": [{
                "id": 1,
                "user_input": "",
                "plan_explanation": "",
                "steps": [
                    {
                        "id": 1,
                        "type": "clean",
                        "status": "done",
                        "last_text": "清洗完成",
                    },
                ],
                "current_step": 0,
                "created_at": "",
            }],
            "current_round": 0,
        }

        pm.save_state(pid, state)
        loaded = pm.load_project(pid)
        steps = loaded["state"]["rounds"][0]["steps"]
        assert steps[0]["last_text"] == "清洗完成"
        assert "last_charts" not in steps[0]

    def test_corrupted_state_handled_gracefully(self, pm):
        """旧版损坏的 state.json（'Figure(...)' 字符串）能被恢复为 Figure 对象"""
        pid = pm.create_project("损坏数据项目")
        state_path = pm.projects_dir / pid / "state.json"

        # 模拟旧版代码写入的损坏数据（旧 flat steps 格式）
        corrupted = {
            "steps": [
                {
                    "id": 1,
                    "type": "eda",
                    "status": "done",
                    "last_charts": ["Figure({'data': [], 'layout': {}})"],  # default=str 的结果
                },
            ],
            "current_step": 0,
        }
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(corrupted, f, ensure_ascii=False)

        # 加载不应崩溃，自动迁移为 rounds 格式并恢复 Figure
        loaded = pm.load_project(pid)
        charts = loaded["state"]["rounds"][0]["steps"][0]["last_charts"]
        assert len(charts) == 1
        assert isinstance(charts[0], go.Figure)


class TestSaveChart:
    def test_save_chart_file(self, pm):
        pid = pm.create_project("图表保存测试")
        fig = px.scatter(x=[1, 2, 3], y=[1, 2, 3])

        path = pm.save_chart(pid, "test_chart", fig)
        assert os.path.exists(path)
        assert path.endswith(".html")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "<html" in content or "plotly" in content.lower()
