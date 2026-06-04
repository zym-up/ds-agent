"""分析项目管理模块"""
import json
import math
import os
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio
from engine import sanitize_json


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
            for step in state.get("steps", []):
                if "last_charts" in step and step["last_charts"]:
                    restored = []
                    for c in step["last_charts"]:
                        if isinstance(c, str):
                            try:
                                restored.append(pio.from_json(c))
                            except (ValueError, KeyError, TypeError):
                                # 旧版损坏数据: Figure(...) repr 字符串 → 尝试提取 JSON
                                try:
                                    import ast
                                    inner = c.strip()
                                    if inner.startswith("Figure("):
                                        inner = inner[7:-1]  # 去掉 "Figure(" 和 ")"
                                    fig_dict = ast.literal_eval(inner)
                                    restored.append(pio.from_json(json.dumps(fig_dict)))
                                except Exception:
                                    pass
                        elif isinstance(c, go.Figure):
                            restored.append(c)
                    step["last_charts"] = restored

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
        state = sanitize_json(state)
        serialized = {"steps": [], "current_step": state.get("current_step", 0)}
        for step in state.get("steps", []):
            s = dict(step)
            if "last_charts" in s and s["last_charts"]:
                s["last_charts"] = [
                    c.to_json() if isinstance(c, go.Figure) else c
                    for c in s["last_charts"]
                ]
            serialized["steps"].append(s)

        pdir = self.projects_dir / project_id
        with open(pdir / "state.json", "w", encoding="utf-8") as f:
            json.dump(serialized, f, ensure_ascii=False, indent=2)

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

    def add_data(self, project_id: str, file_path: str) -> str:
        """保存为新数据文件，后续可通过 merge_selected_data 合并。返回存储路径。"""
        pdir = self.projects_dir / project_id / "data"
        pdir.mkdir(parents=True, exist_ok=True)
        existing_files = list(pdir.glob("data_*.csv"))
        new_index = len(existing_files) + 1
        dest = pdir / f"data_{new_index}.csv"
        new_df = pd.read_csv(file_path) if file_path.endswith(".csv") else pd.read_excel(file_path)
        new_df.to_csv(dest, index=False)
        return str(dest)

    def list_data_files(self, project_id: str) -> list:
        """列出项目所有数据文件，返回 [{name, path, rows}]"""
        pdir = self.projects_dir / project_id / "data"
        if not pdir.exists():
            return []
        files = []
        for f in sorted(pdir.glob("*.csv")):
            df = pd.read_csv(f)
            files.append({"name": f.name, "path": str(f), "rows": len(df)})
        return files

    def merge_selected_data(self, project_id: str, selected_files: list) -> "pd.DataFrame":
        """按勾选文件名列表，合并数据（按列名匹配，按行拼接）"""
        pdir = self.projects_dir / project_id / "data"
        dfs = []
        for fname in selected_files:
            fpath = pdir / fname
            if fpath.exists():
                dfs.append(pd.read_csv(fpath))
        if not dfs:
            raise ValueError("没有找到选中的数据文件")
        return pd.concat(dfs, ignore_index=True)

    def list_reports(self, project_id: str) -> list:
        """列出项目所有报告，返回 [{name, path, created_at}]"""
        pdir = self.projects_dir / project_id / "reports"
        reports = []
        for f in sorted(pdir.glob("report_*.html"), reverse=True):
            stat = f.stat()
            reports.append({
                "name": f.name,
                "path": str(f),
                "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
            })
        return reports

    def get_project_info(self, project_id: str) -> dict:
        """获取项目元信息"""
        pdir = self.projects_dir / project_id
        if not pdir.exists():
            raise FileNotFoundError(f"项目 {project_id} 不存在")
        with open(pdir / "meta.json", "r", encoding="utf-8") as f:
            meta = json.load(f)
        data_files = self.list_data_files(project_id)
        total_rows = sum(f["rows"] for f in data_files)
        reports = self.list_reports(project_id)
        state_path = pdir / "state.json"
        steps_count = 0
        if state_path.exists():
            with open(state_path, "r", encoding="utf-8") as f:
                state = json.load(f)
                steps_count = len(state.get("steps", []))
        return {
            "name": meta["name"],
            "created_at": meta["created_at"],
            "data_files_count": len(data_files),
            "total_rows": total_rows,
            "steps_count": steps_count,
            "reports_count": len(reports),
        }
