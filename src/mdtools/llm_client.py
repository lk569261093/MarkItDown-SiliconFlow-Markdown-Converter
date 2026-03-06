"""SiliconFlow 兼容 OpenAI SDK 的流式客户端。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from openai import OpenAI

from .config import (
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_USER_PROMPT_TEMPLATE,
    LLMSettings,
    normalize_base_url,
)


@dataclass(slots=True)
class StreamDelta:
    """流式增量内容。"""

    content: str = ""
    reasoning_content: str = ""


class SiliconFlowMarkdownClient:
    """对接 SiliconFlow 聊天补全流式接口。"""

    def __init__(self, settings: LLMSettings) -> None:
        self.settings = settings
        self._client = OpenAI(
            api_key=settings.api_key,
            base_url=normalize_base_url(settings.base_url),
        )

    def stream_refine_markdown(
        self,
        markdown_chunk: str,
        source_name: str,
        chunk_index: int,
        total_chunks: int,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        user_prompt_template: str = DEFAULT_USER_PROMPT_TEMPLATE,
    ) -> Iterator[StreamDelta]:
        """流式处理单个分块，逐步返回模型输出。"""
        user_prompt = user_prompt_template.format(
            source_name=source_name,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            markdown_chunk=markdown_chunk,
        )

        response = self._client.chat.completions.create(
            model=self.settings.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.settings.temperature,
            max_tokens=self.settings.max_tokens,
            stream=True,
        )

        for chunk in response:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta
            content = getattr(delta, "content", "") or ""
            reasoning_content = getattr(delta, "reasoning_content", "") or ""

            if content or reasoning_content:
                yield StreamDelta(content=content, reasoning_content=reasoning_content)
