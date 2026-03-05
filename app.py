from __future__ import annotations

import io
import zipfile
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import streamlit as st

from src.mdtools.config import (
    DEFAULT_API_KEY_PLACEHOLDER,
    DEFAULT_BASE_URL,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    LLMSettings,
)
from src.mdtools.converter import DocumentConverter
from src.mdtools.file_utils import (
    build_output_filename,
    concat_chunks,
    split_markdown_text,
)
from src.mdtools.llm_client import SiliconFlowMarkdownClient
from src.mdtools.model_catalog import fetch_user_models

MODEL_GUIDANCE = [
    {
        "Scenario": "Scanned PDF/OCR",
        "Recommended Model": "deepseek-ai/DeepSeek-OCR",
        "Notes": "官方文档给出文档转 Markdown 示例，适合版面复杂和公式场景。",
    },
    {
        "Scenario": "Image + Text Understanding",
        "Recommended Model": "Qwen/Qwen2.5-VL-72B-Instruct",
        "Notes": "适合图文混排内容，可用于补充提取公式与图表描述。",
    },
    {
        "Scenario": "Formula Cleanup/Reasoning",
        "Recommended Model": "deepseek-ai/DeepSeek-R1",
        "Notes": "支持 reasoning_content，适合做公式规范化与逻辑校验。",
    },
]


def mask_api_key(api_key: str) -> str:
    """将 API Key 脱敏显示为 sk-**** 形式。"""
    key = api_key.strip()
    if not key:
        return "sk-********************************"

    if len(key) <= 10:
        return "sk-******"

    return f"{key[:5]}{'*' * (len(key) - 9)}{key[-4:]}"


def render_sidebar() -> dict:
    """渲染侧边栏配置并返回参数。"""
    st.sidebar.header("LLM Configuration")
    api_key = st.sidebar.text_input(
        "API Key",
        value="",
        type="password",
        placeholder=DEFAULT_API_KEY_PLACEHOLDER,
        help="Format: sk-xxxxxxxxxxxxxxxx (masked preview shown below).",
    )
    st.sidebar.caption(f"Masked API Key Preview: `{mask_api_key(api_key)}`")
    base_url = st.sidebar.text_input("Base URL", value=DEFAULT_BASE_URL)
    model = st.sidebar.text_input("Model", value=DEFAULT_MODEL)
    model_type = st.sidebar.selectbox(
        "Model Type",
        options=["text", "image"],
        index=0,
        help="用于从 /models 接口筛选模型列表。",
    )
    model_sub_type = st.sidebar.text_input("Model Sub Type", value="chat")

    if "available_models" not in st.session_state:
        st.session_state["available_models"] = []

    if st.sidebar.button("Fetch Available Models"):
        if not api_key.strip():
            st.sidebar.error("Please fill API Key before fetching models.")
        else:
            try:
                st.session_state["available_models"] = fetch_user_models(
                    api_key=api_key.strip(),
                    base_url=base_url.strip(),
                    model_type=model_type,
                    sub_type=model_sub_type.strip(),
                )
                st.sidebar.success(f"Loaded {len(st.session_state['available_models'])} models.")
            except Exception as exc:
                st.sidebar.error(f"Fetch models failed: {exc}")

    if st.session_state["available_models"]:
        selected = st.sidebar.selectbox(
            "Available Models",
            options=st.session_state["available_models"],
            index=0,
        )
        use_selected = st.sidebar.toggle("Use Selected Model", value=True)
        if use_selected:
            model = selected

    st.sidebar.divider()
    enable_llm = st.sidebar.toggle("Enable LLM Post-Processing", value=True)
    show_reasoning = st.sidebar.toggle("Show Reasoning Stream", value=False)
    chunk_size = st.sidebar.slider(
        "Chunk Size (chars)",
        min_value=4000,
        max_value=24000,
        value=DEFAULT_CHUNK_SIZE,
        step=1000,
    )
    temperature = st.sidebar.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=DEFAULT_TEMPERATURE,
        step=0.1,
    )
    max_tokens = st.sidebar.number_input(
        "Max Tokens",
        min_value=512,
        max_value=16384,
        value=DEFAULT_MAX_TOKENS,
        step=256,
    )

    return {
        "api_key": api_key.strip(),
        "base_url": base_url.strip(),
        "model": model.strip(),
        "model_type": model_type,
        "model_sub_type": model_sub_type.strip(),
        "enable_llm": enable_llm,
        "show_reasoning": show_reasoning,
        "chunk_size": int(chunk_size),
        "temperature": float(temperature),
        "max_tokens": int(max_tokens),
    }


def run_llm_refine(
    client: SiliconFlowMarkdownClient,
    source_name: str,
    markdown: str,
    chunk_size: int,
    show_reasoning: bool,
) -> str:
    """按分块进行流式优化，并实时展示输出。"""
    chunks = split_markdown_text(markdown, max_chars=chunk_size)
    total = len(chunks)
    refined_chunks: list[str] = []

    progress = st.progress(0.0)
    status = st.empty()
    stream_box = st.empty()
    reasoning_box = st.empty()

    for idx, chunk in enumerate(chunks, start=1):
        status.info(f"LLM streaming chunk {idx}/{total} ...")
        chunk_output = ""
        reasoning_output = ""

        try:
            for delta in client.stream_refine_markdown(
                markdown_chunk=chunk,
                source_name=source_name,
                chunk_index=idx,
                total_chunks=total,
            ):
                if delta.content:
                    chunk_output += delta.content
                    stream_box.code(chunk_output[-6000:], language="markdown")

                if show_reasoning and delta.reasoning_content:
                    reasoning_output += delta.reasoning_content
                    reasoning_box.text(reasoning_output[-2000:])

        except Exception as exc:
            st.warning(f"Chunk {idx} processing failed, fallback to original text. Error: {exc}")
            chunk_output = chunk

        refined_chunks.append(chunk_output.strip() or chunk)
        progress.progress(idx / total)

    status.success("LLM post-processing completed.")
    return concat_chunks(refined_chunks)


def process_files(
    uploaded_files: list,
    options: dict,
) -> list[tuple[str, str]]:
    """处理上传文件并返回可下载结果。"""
    converter = DocumentConverter()
    outputs: list[tuple[str, str]] = []

    llm_client = None
    if options["enable_llm"]:
        llm_settings = LLMSettings(
            api_key=options["api_key"],
            base_url=options["base_url"],
            model=options["model"],
            temperature=options["temperature"],
            max_tokens=options["max_tokens"],
        )
        llm_client = SiliconFlowMarkdownClient(llm_settings)

    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        for index, uploaded in enumerate(uploaded_files, start=1):
            st.subheader(f"[{index}] {uploaded.name}")
            safe_name = Path(uploaded.name).name
            input_path = tmp_path / safe_name
            input_path.write_bytes(uploaded.getbuffer())

            try:
                converted = converter.convert_to_markdown(input_path)
            except Exception as exc:
                st.error(f"MarkItDown convert failed: {exc}")
                continue

            raw_markdown = converted.markdown.strip()
            if not raw_markdown:
                st.warning("No markdown content extracted from this file.")
                continue

            with st.expander("Raw Markdown (MarkItDown)", expanded=False):
                st.code(raw_markdown[:12000], language="markdown")

            final_markdown = raw_markdown
            if llm_client is not None:
                final_markdown = run_llm_refine(
                    client=llm_client,
                    source_name=uploaded.name,
                    markdown=raw_markdown,
                    chunk_size=options["chunk_size"],
                    show_reasoning=options["show_reasoning"],
                )

            output_name = build_output_filename(uploaded.name, suffix="markdown")
            outputs.append((output_name, final_markdown))

            with st.expander("Final Markdown Preview", expanded=True):
                st.code(final_markdown[:12000], language="markdown")

            st.download_button(
                label=f"Download {output_name}",
                data=final_markdown.encode("utf-8"),
                file_name=output_name,
                mime="text/markdown",
                key=f"download_{index}_{uploaded.name}",
            )

    return outputs


def render_bulk_download(outputs: list[tuple[str, str]]) -> None:
    """将全部结果打包为 ZIP。"""
    if not outputs:
        return

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for filename, content in outputs:
            archive.writestr(filename, content.encode("utf-8"))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"markdown_outputs_{timestamp}.zip"

    st.download_button(
        label="Download All as ZIP",
        data=zip_buffer.getvalue(),
        file_name=zip_name,
        mime="application/zip",
    )


def main() -> None:
    st.set_page_config(page_title="MarkItDown + SiliconFlow", page_icon="📝", layout="wide")
    st.title("MarkItDown + SiliconFlow Markdown Converter")
    st.caption(
        "Upload PDF/Word and other supported files, convert via MarkItDown, "
        "then optionally refine Markdown using SiliconFlow streaming output."
    )

    options = render_sidebar()

    st.info(
        "Supported file types depend on MarkItDown and your local dependencies. "
        "If a format fails, install related parsers and retry."
    )
    with st.expander("Model Recommendations for Formula-Rich Documents", expanded=False):
        st.table(MODEL_GUIDANCE)

    files = st.file_uploader(
        "Upload files",
        accept_multiple_files=True,
        help="MarkItDown supports many formats. Unsupported files will be skipped with error messages.",
    )

    run_clicked = st.button("Start Conversion", type="primary", disabled=not files)
    if not run_clicked:
        return

    if options["enable_llm"] and not options["api_key"]:
        st.error("Please fill API Key in the sidebar before enabling LLM post-processing.")
        return

    with st.spinner("Processing files, please wait..."):
        outputs = process_files(files or [], options)

    if not outputs:
        st.warning("No successful conversion results.")
        return

    st.success(f"Completed: {len(outputs)} file(s).")
    render_bulk_download(outputs)


if __name__ == "__main__":
    main()
