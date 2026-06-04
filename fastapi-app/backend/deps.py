"""共享依赖：ProjectManager、Agent 缓存、工具函数"""
import os
import logging

from engine.config import load_config
from engine.llm_agent import LLMAdapter, AnalysisAgent
from engine.project_manager import ProjectManager

logger = logging.getLogger(__name__)

pm = ProjectManager()
_agent_cache: dict = {}


def get_agent(project_id: str = None):
    """获取 AnalysisAgent 实例（按 project_id 缓存以保持对话连续）"""
    if project_id and project_id in _agent_cache:
        return _agent_cache[project_id]
    config = load_config()
    adapter = LLMAdapter(config.llm)
    agent = AnalysisAgent(adapter)
    if project_id:
        try:
            project_data = pm.load_project(project_id)
            if project_data.get("chat_history"):
                agent.set_chat_history(project_data["chat_history"])
        except Exception:
            pass
        _agent_cache[project_id] = agent
    return agent


def load_chart_html(project_id: str, step_index: int) -> str:
    """从磁盘加载步骤关联的图表 HTML"""
    chart_dir = os.path.join("projects", project_id, "charts")
    html_parts = []
    j = 1
    while j <= 100:
        chart_path = os.path.join(chart_dir, f"step{step_index + 1}_chart{j}.html")
        if os.path.exists(chart_path):
            with open(chart_path, "r", encoding="utf-8") as f:
                html_parts.append(f.read())
            j += 1
        else:
            break
    return "".join(html_parts)
