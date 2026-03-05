"""模型列表拉取工具。"""

from __future__ import annotations

from typing import List

import requests

from .config import normalize_base_url


def fetch_user_models(
    api_key: str,
    base_url: str,
    model_type: str = "text",
    sub_type: str = "chat",
    timeout: int = 20,
) -> List[str]:
    """调用 SiliconFlow /models 接口，返回可用模型 ID。"""
    endpoint = f"{normalize_base_url(base_url).rstrip('/')}/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"type": model_type, "sub_type": sub_type}

    response = requests.get(endpoint, headers=headers, params=params, timeout=timeout)
    response.raise_for_status()

    payload = response.json()
    records = payload.get("data", [])
    model_ids = [item.get("id", "") for item in records if item.get("id")]
    return sorted(set(model_ids))
