# mdtools

一个可工程化部署的文档转 Markdown 工具，基于 **Streamlit + MarkItDown + SiliconFlow(OpenAI 兼容接口)**。

## 功能特性

- 支持多文件上传并批量转换为 Markdown。
- 使用 MarkItDown 做基础解析（PDF/Word/PPT/Excel/图片等，具体依赖本地环境）。
- 支持 SiliconFlow 流式输出，对 Markdown 二次整理（结构修复、公式规范化）。
- 支持单文件下载与 ZIP 打包下载。
- 支持调用 `/models` 接口拉取可用模型。

- API Key 输入框为密码模式，并提供脱敏预览，避免明文泄露。
- 已默认包含 `markitdown[pdf]` 依赖，可直接处理 PDF 文件。

## 当前默认配置（可在界面修改）

- Base URL: `https://api.siliconflow.cn`
- Default Model: `deepseek-ai/DeepSeek-R1`
- Temperature: `0.1`
- Max Tokens: `4096`
- Chunk Size: `12000`


## 项目结构

```text
mdtools/
├─ app.py
├─ requirements.txt
├─ runtime.txt
├─ .gitignore
├─ .streamlit/
│  └─ config.toml
└─ src/
   └─ mdtools/
      ├─ config.py
      ├─ converter.py
      ├─ file_utils.py
      ├─ llm_client.py
      └─ model_catalog.py
```

## 安装与运行

```bash
# 1) 创建虚拟环境
python -m venv .venv

# 2) 激活（Windows PowerShell）
.\.venv\Scripts\Activate.ps1

# 3) 安装依赖（清华镜像）
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 如果你是旧环境升级，单独补齐 PDF 依赖
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -U "markitdown[pdf]"

# 4) 启动
streamlit run app.py
```

## 使用步骤

1. 在侧边栏填写 API Key（不会显示完整明文）。
2. 可选：点击 `Fetch Available Models` 拉取模型列表。
3. 上传待转换文件。
4. 点击 `Start Conversion`，等待流式处理完成。
5. 下载单个 `.md` 或整体 `ZIP`。

## 模型建议


- 默认推荐：`deepseek-ai/DeepSeek-R1`
- 如需尝试其他模型，保持“默认 R1 + 可手动切换”的方式即可。
- 默认推荐：`deepseek-ai/DeepSeek-R1`（当前测试效果最佳）。



- 本项目不保存 API Key 明文。
- 已提供 `.gitignore`，忽略缓存、虚拟环境、备份文件等本地内容。
- 已提供 `runtime.txt`（`python-3.10`）以减少云端环境差异。

## Streamlit Cloud 部署排错（PDF 依赖）

如果云端出现 `PdfConverter MissingDependencyException`，按下面顺序处理：

1. 确认部署分支已包含最新 `requirements.txt` 与 `runtime.txt`。
2. 在 Streamlit Cloud 中执行 **Reboot app** 和 **Clear cache** 后重新部署。
3. 查看构建日志，确认已安装 `markitdown[pdf]`、`pdfplumber`、`pdfminer.six`。
4. 若仍失败，删除旧应用后新建一次（避免旧镜像缓存）。


## 参考链接

- SiliconFlow 用户指南：https://docs.siliconflow.cn/cn/userguide/introduction
- SiliconFlow 模型列表接口：https://docs.siliconflow.cn/cn/api-reference/models/list-models
- MarkItDown：https://github.com/microsoft/markitdown
