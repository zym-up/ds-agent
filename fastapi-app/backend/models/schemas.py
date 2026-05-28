"""Pydantic 数据模型"""
from pydantic import BaseModel
from typing import Optional


class LLMConfigSchema(BaseModel):
    name: str = "DeepSeek"
    base_url: str = ""
    api_key: str = ""
    model: str = ""
    temperature: float = 0.3
    max_tokens: int = 4096


class AnalysisRequest(BaseModel):
    project_id: str
    user_input: str


class StepExecuteRequest(BaseModel):
    project_id: str
    step_index: int


class GenerateReportRequest(BaseModel):
    project_id: str
    title: str
    step_indices: list[int] = []
    user_notes: str = ""
    include_conclusion: bool = True


class MergeDataRequest(BaseModel):
    selected_files: list[str]


class ConcludeRequest(BaseModel):
    project_id: str
    step_indices: list[int] = []
    user_notes: str = ""


class PlanStreamRequest(BaseModel):
    project_id: str
    user_input: str


class ExecuteStreamRequest(BaseModel):
    project_id: str
    step_index: int
