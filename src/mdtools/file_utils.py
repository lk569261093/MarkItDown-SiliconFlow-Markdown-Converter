"""文件与文本处理工具。"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Iterable, List


def split_markdown_text(markdown: str, max_chars: int) -> List[str]:
    """按段落分块，避免超出模型上下文。"""
    content = markdown.strip()
    if not content:
        return [""]

    if len(content) <= max_chars:
        return [content]

    chunks: list[str] = []
    buffer = ""

    for paragraph in content.split("\n\n"):
        candidate = f"{buffer}\n\n{paragraph}".strip() if buffer else paragraph
        if len(candidate) <= max_chars:
            buffer = candidate
            continue

        if buffer:
            chunks.append(buffer)
            buffer = ""

        if len(paragraph) <= max_chars:
            buffer = paragraph
            continue

        # 超长段落按定长切分，保证流程可继续
        for idx in range(0, len(paragraph), max_chars):
            chunks.append(paragraph[idx : idx + max_chars])

    if buffer:
        chunks.append(buffer)

    return chunks


def sanitize_filename_stem(name: str) -> str:
    """清理文件名，避免系统不兼容字符。"""
    stem = Path(name).stem
    cleaned = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff._-]+", "_", stem)
    return cleaned.strip("._") or "converted"


def build_output_filename(source_name: str, suffix: str = "converted") -> str:
    """输出文件名包含源文件名与秒级时间戳。"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = sanitize_filename_stem(source_name)
    return f"{stem}_{suffix}_{timestamp}.md"


def concat_chunks(chunks: Iterable[str]) -> str:
    """拼接分块文本。"""
    return "\n\n".join(chunk.strip() for chunk in chunks if chunk is not None).strip()
