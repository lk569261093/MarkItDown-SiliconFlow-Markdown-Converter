"""应用配置与常量。"""

from __future__ import annotations

from dataclasses import dataclass

# 默认配置：允许用户在界面中覆盖
DEFAULT_BASE_URL = "https://api.siliconflow.cn"
DEFAULT_MODEL = "deepseek-ai/DeepSeek-R1"
DEFAULT_API_KEY_PLACEHOLDER = "sk-********************************"

# 兼顾常见办公文档与 MarkItDown 常见输入格式
SUPPORTED_EXTENSIONS = [
    ".pdf",
    ".docx",
    ".doc",
    ".pptx",
    ".ppt",
    ".xlsx",
    ".xls",
    ".csv",
    ".txt",
    ".md",
    ".html",
    ".htm",
    ".xml",
    ".json",
    ".epub",
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".gif",
    ".tiff",
]

UPLOAD_FILE_TYPES = [ext.lstrip(".") for ext in SUPPORTED_EXTENSIONS]

DEFAULT_CHUNK_SIZE = 12000
DEFAULT_TEMPERATURE = 0.1
DEFAULT_MAX_TOKENS = 4096

DEFAULT_SYSTEM_PROMPT = (
    "你是高质量 Markdown 技术编辑。"
    "请在不改变原始含义的前提下，修复格式并将数学表达式统一为 Markdown 可读形式。"
    "对于可识别的公式，优先使用 LaTeX 语法（行内用$...$，块级用$$...$$）。"
    "严禁编造不存在的数据、结论和参考文献。"
)

DEFAULT_USER_PROMPT_TEMPLATE = """请处理下面这段由 MarkItDown 生成的内容：

要求：
1. 保留原文信息，不删减关键内容。
2. 修复标题层级、列表、表格、代码块与引用格式。
3. 对可能的数学公式进行规范化输出。
4. 不要输出解释，只返回最终 Markdown。

源文件：{source_name}
分块：{chunk_index}/{total_chunks}

```markdown
{markdown_chunk}
```
"""


@dataclass(slots=True)
class LLMSettings:
    """LLM 运行参数。"""

    api_key: str
    base_url: str
    model: str
    temperature: float = DEFAULT_TEMPERATURE
    max_tokens: int = DEFAULT_MAX_TOKENS


def normalize_base_url(base_url: str) -> str:
    """规范化 SiliconFlow 接口地址，确保末尾带 /v1。"""
    cleaned = base_url.strip().rstrip("/")
    if not cleaned.endswith("/v1"):
        cleaned = f"{cleaned}/v1"
    return cleaned
