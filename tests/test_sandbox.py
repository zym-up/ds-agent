"""sandbox 安全执行环境测试"""
import pytest
from engine.sandbox import validate_code, run_sandbox


# ── validate_code ──
def test_validate_safe_code():
    ok, err = validate_code("a = 1 + 2\nb = a * 3")
    assert ok
    assert err is None

def test_validate_safe_import():
    ok, err = validate_code("import numpy as np\nimport pandas as pd")
    assert ok

def test_validate_forbidden_import_os():
    ok, err = validate_code("import os\nos.system('dir')")
    assert not ok
    assert "禁止" in err

def test_validate_forbidden_import_subprocess():
    ok, err = validate_code("import subprocess")
    assert not ok

def test_validate_forbidden_import_socket():
    ok, err = validate_code("import socket")
    assert not ok

def test_validate_forbidden_eval():
    ok, err = validate_code("eval('1+1')")
    assert not ok

def test_validate_forbidden_exec():
    ok, err = validate_code("exec('x=1')")
    assert not ok

def test_validate_forbidden_open():
    ok, err = validate_code("open('/etc/passwd')")
    assert not ok

def test_validate_forbidden_compile():
    ok, err = validate_code("compile('a', '', 'exec')")
    assert not ok

def test_validate_string_containing_module_name():
    """代码字符串中含 'os' 但不是 import 语句，不应拦截"""
    ok, err = validate_code("a = 'cost'\nb = 'close'\nprint(a)")
    assert ok

def test_validate_allowed_imports():
    for mod in ["pandas", "numpy", "scipy", "sklearn", "plotly",
                "json", "csv", "math", "statistics", "collections"]:
        ok, err = validate_code(f"import {mod}")
        assert ok, f"模块 {mod} 应该被允许"


# ── run_sandbox ──
def test_run_sandbox_success():
    ok, stdout, stderr = run_sandbox("print('hello')")
    assert ok
    assert "hello" in stdout

def test_run_sandbox_syntax_error():
    ok, stdout, stderr = run_sandbox("print('oops'")
    assert not ok

def test_run_sandbox_forbidden():
    ok, stdout, stderr = run_sandbox("import os")
    assert not ok
    assert "禁止" in stderr

def test_run_sandbox_timeout():
    ok, stdout, stderr = run_sandbox("while True: pass", timeout=2)
    assert not ok
    assert "超时" in stderr
