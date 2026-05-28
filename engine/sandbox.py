"""安全代码执行沙箱"""
import subprocess
import tempfile
import os
import re
from typing import Optional


FORBIDDEN_IMPORTS = [
    "os", "subprocess", "sys", "shutil", "socket", "requests",
    "urllib", "http", "ftplib", "telnetlib", "smtplib",
    "pickle", "marshal", "ctypes", "multiprocessing",
    "importlib", "eval", "exec", "compile",
]

FORBIDDEN_FUNCTIONS = [
    "open(", "exec(", "eval(", "compile(", "__import__(",
    "globals()", "locals()", "getattr(", "setattr(", "delattr(",
]

ALLOWED_IMPORTS = [
    "pandas", "numpy", "scipy", "sklearn", "plotly", "matplotlib",
    "json", "csv", "math", "statistics", "collections", "itertools",
    "functools", "datetime", "typing", "warnings",
]


def validate_code(code: str) -> tuple:
    """验证代码安全性"""
    for imp in FORBIDDEN_IMPORTS:
        pattern = rf'\bimport\s+{imp}\b|\bfrom\s+{imp}\b'
        if re.search(pattern, code):
            if imp not in ALLOWED_IMPORTS:
                return False, f"禁止使用模块: {imp}"

    for func in FORBIDDEN_FUNCTIONS:
        if func in code:
            return False, f"禁止使用函数: {func}"

    return True, None


def run_sandbox(code: str, timeout: int = 30) -> tuple:
    """在子进程中安全执行 Python 代码, 返回: (success, stdout, stderr)"""
    is_safe, error = validate_code(code)
    if not is_safe:
        return False, "", error

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(code)
        tmp_path = f.name

    try:
        result = subprocess.run(
            ["python", tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.getcwd(),
            env={
                "PATH": os.environ.get("PATH", ""),
                "PYTHONPATH": os.getcwd(),
            },
        )
        success = result.returncode == 0
        return success, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"代码执行超时 ({timeout}秒)"
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
