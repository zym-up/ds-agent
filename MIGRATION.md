# 迁移指南 — 如何在新电脑上运行

## 方式一：直接拷贝（推荐）

### 需要拷贝的内容

整个项目文件夹拷到新电脑上，**除了这两个可以删掉省空间**：

- `venv/` — 虚拟环境（在新电脑上重新创建）
- `fastapi-app/frontend/node_modules/` — 前端依赖（在新电脑上重新安装）

### 新电脑上需要预装

| 软件 | 下载地址 | 备注 |
|------|---------|------|
| Python 3.11+ | https://www.python.org/downloads/ | 安装时勾选 "Add Python to PATH" |
| Node.js (仅 FastAPI+Vue 版需要) | https://nodejs.org/ | 安装 LTS 版本即可 |

### 安装步骤

1. 把项目文件夹拷到新电脑
2. 双击 `setup.bat`，等待依赖安装完成
3. 安装完成后：
   - **Streamlit 版**: 双击 `streamlit-app/run.bat`
   - **FastAPI+Vue 版**: 先双击 `fastapi-app/run_backend.bat` 启动后端，再双击 `fastapi-app/run_frontend.bat` 启动前端

### Streamlit 版访问

浏览器打开 `http://localhost:8501`

### FastAPI+Vue 版访问

- 后端 API 文档: `http://localhost:8502/docs`
- 前端界面: `http://localhost:5173`

---

## 方式二：U盘/压缩包

把整个项目文件夹打成 zip，拷到新电脑解压，然后按方式一的步骤操作。

**打包前建议删除：**
- `venv/` 文件夹
- `fastapi-app/frontend/node_modules/` 文件夹
- `projects/` 文件夹（用户项目数据，看情况保留）

---

## 首次使用配置

1. 打开应用后，进入「设置」页面
2. 填入公司内网 LLM API 的地址和 Key
3. 点击「测试连接」确认能通
4. 点击「保存配置」
5. 开始使用

---

## 领域知识库自定义

编辑 `knowledge/indicators.yaml` 可以添加自己领域的物理指标知识。
编辑 `knowledge/templates.yaml` 可以添加常用分析模板。
在 `knowledge/references/` 目录下放 `.txt` 或 `.md` 文件，可以扩展参考文档。

修改后重启应用即可生效。
