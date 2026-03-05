"""MarkItDown 转换封装。"""

from __future__ import annotations

import cgi
import html
from dataclasses import dataclass
from pathlib import Path

# 兼容旧依赖仍调用 cgi.escape 的场景（Python 3.8+ 已移除该函数）
if not hasattr(cgi, "escape"):
    cgi.escape = html.escape  # type: ignore[attr-defined]

from markitdown import MarkItDown


@dataclass(slots=True)
class ConvertedDocument:
    """单个文件的转换结果。"""

    source_name: str
    source_path: Path
    markdown: str


class DocumentConverter:
    """统一管理 MarkItDown 的调用。"""

    def __init__(self) -> None:
        self._converter = MarkItDown()

    def convert_to_markdown(self, file_path: Path) -> ConvertedDocument:
        """将本地文件转换为 Markdown 文本。"""
        result = self._converter.convert(str(file_path))
        markdown = getattr(result, "text_content", "") or ""
        if not markdown.strip():
            markdown = str(result)

        return ConvertedDocument(
            source_name=file_path.name,
            source_path=file_path,
            markdown=markdown,
        )