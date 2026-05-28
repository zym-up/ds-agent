"""全局配置管理"""
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
from typing import Optional


@dataclass
class LLMConfig:
    name: str = "DeepSeek"
    base_url: str = "https://api.deepseek.com/v1"
    api_key: str = ""
    model: str = "deepseek-chat"
    temperature: float = 0.3
    max_tokens: int = 4096

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "LLMConfig":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class AppConfig:
    llm: LLMConfig = field(default_factory=LLMConfig)
    projects_dir: str = "projects"
    knowledge_dir: str = "knowledge"
    data_dir: str = "data"

    def to_dict(self) -> dict:
        return {
            "llm": self.llm.to_dict(),
            "projects_dir": self.projects_dir,
            "knowledge_dir": self.knowledge_dir,
            "data_dir": self.data_dir,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "AppConfig":
        llm = LLMConfig.from_dict(d.get("llm", {}))
        return cls(
            llm=llm,
            projects_dir=d.get("projects_dir", "projects"),
            knowledge_dir=d.get("knowledge_dir", "knowledge"),
            data_dir=d.get("data_dir", "data"),
        )


def load_config(config_path: str = "config.json") -> AppConfig:
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return AppConfig.from_dict(json.load(f))
    return AppConfig()


def save_config(config: AppConfig, config_path: str = "config.json") -> None:
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)


LLM_PRESETS = {
    "deepseek": LLMConfig(
        name="DeepSeek",
        base_url="https://api.deepseek.com/v1",
        model="deepseek-chat",
        temperature=0.3,
        max_tokens=4096,
    ),
    "qwen": LLMConfig(
        name="Qwen",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen-plus",
        temperature=0.3,
        max_tokens=4096,
    ),
    "custom": LLMConfig(
        name="自定义",
        base_url="",
        model="",
        temperature=0.3,
        max_tokens=4096,
    ),
}
