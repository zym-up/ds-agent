"""分析项目管理模块"""
import json
import os
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
import pandas as pd


class ProjectManager:
    """管理分析项目的创建、保存、加载"""

    def __init__(self, projects_dir: str = "projects"):
        self.projects_dir = Path(projects_dir)
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def create_project(self, name: str, data_file: Optional[str] = None) -> str:
        """创建新项目，返回 project_id"""
        project_id = uuid.uuid4().hex[:12]
        project_path = self.projects_dir / project_id
        project_path.mkdir(parents=True)
        (project_path / "data").mkdir()
        (project_path / "charts").mkdir()
        (project_path / "reports").mkdir()

        meta = {
            "name": name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "data_file": os.path.basename(data_file) if data_file else None,
        }
        with open(project_path / "meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        with open(project_path / "state.json", "w", encoding="utf-8") as f:
            json.dump({"steps": [], "current_step": 0}, f, ensure_ascii=False, indent=2)

        with open(project_path / "chat_history.json", "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

        if data_file and os.path.exists(data_file):
            df = pd.read_csv(data_file) if data_file.endswith(".csv") else pd.read_excel(data_file)
            df.to_csv(project_path / "data" / "original.csv", index=False)

        return project_id

    def list_projects(self) -> list:
        """列出所有项目"""
        projects = []
        for pdir in self.projects_dir.iterdir():
            if pdir.is_dir():
                meta_path = pdir / "meta.json"
                if meta_path.exists():
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    state_path = pdir / "state.json"
                    steps_count = 0
                    if state_path.exists():
                        with open(state_path, "r", encoding="utf-8") as f:
                            state = json.load(f)
                            steps_count = len(state.get("steps", []))
                    projects.append({
                        "id": pdir.name,
                        **meta,
                        "steps_count": steps_count,
                    })
        projects.sort(key=lambda p: p["created_at"], reverse=True)
        return projects

    def load_project(self, project_id: str) -> dict:
        """加载项目完整数据"""
        pdir = self.projects_dir / project_id
        if not pdir.exists():
            raise FileNotFoundError(f"项目 {project_id} 不存在")

        with open(pdir / "meta.json", "r", encoding="utf-8") as f:
            meta = json.load(f)

        state = {"steps": [], "current_step": 0}
        state_path = pdir / "state.json"
        if state_path.exists():
            with open(state_path, "r", encoding="utf-8") as f:
                state = json.load(f)

        chat_history = []
        chat_path = pdir / "chat_history.json"
        if chat_path.exists():
            with open(chat_path, "r", encoding="utf-8") as f:
                chat_history = json.load(f)

        df = None
        data_path = pdir / "data" / "original.csv"
        if data_path.exists():
            df = pd.read_csv(data_path)

        return {
            "meta": meta,
            "state": state,
            "chat_history": chat_history,
            "dataframe": df,
        }

    def save_state(self, project_id: str, state: dict) -> None:
        """保存分析状态"""
        pdir = self.projects_dir / project_id
        with open(pdir / "state.json", "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2, default=str)

        meta_path = pdir / "meta.json"
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        meta["updated_at"] = datetime.now().isoformat()
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    def save_chat_history(self, project_id: str, chat_history: list) -> None:
        """保存对话历史"""
        pdir = self.projects_dir / project_id
        with open(pdir / "chat_history.json", "w", encoding="utf-8") as f:
            json.dump(chat_history, f, ensure_ascii=False, indent=2)

    def save_chart(self, project_id: str, chart_name: str, fig) -> str:
        """保存图表文件，返回路径"""
        pdir = self.projects_dir / project_id / "charts"
        filepath = pdir / f"{chart_name}.html"
        fig.write_html(str(filepath))
        return str(filepath)

    def save_report(self, project_id: str, html_content: str) -> str:
        """保存报告文件，返回路径"""
        pdir = self.projects_dir / project_id / "reports"
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = pdir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        return str(filepath)

    def delete_project(self, project_id: str) -> None:
        """删除项目"""
        pdir = self.projects_dir / project_id
        if pdir.exists():
            shutil.rmtree(pdir)

    def rename_project(self, project_id: str, new_name: str) -> None:
        """重命名项目"""
        pdir = self.projects_dir / project_id
        meta_path = pdir / "meta.json"
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        meta["name"] = new_name
        meta["updated_at"] = datetime.now().isoformat()
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
