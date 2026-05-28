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
    conclusion: str = ""
