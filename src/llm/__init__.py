"""
LLM 客户端模块

[INPUT]: 环境变量配置
[OUTPUT]: LLM 客户端实例和工具函数
[POS]: 提供共享的 LLM 配置和 JSON 解析工具
"""

import os
import json
import re
from typing import Optional

from langchain_openai import ChatOpenAI


def get_llm_client() -> ChatOpenAI:
    """
    获取 LLM 客户端实例

    Returns:
        ChatOpenAI 实例
    """
    api_key = os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("OPENAI_API_BASE")
    model_name = os.getenv("OPENAI_MODEL_NAME", "qwen-plus")

    if not api_key:
        raise ValueError("未配置 OPENAI_API_KEY 环境变量")

    return ChatOpenAI(
        model=model_name,
        temperature=0,
        api_key=api_key,
        base_url=api_base if api_base else None,
    )


def parse_json_from_llm_response(content: str) -> Optional[dict]:
    """
    从 LLM 响应中解析 JSON

    支持以下格式：
    - 纯 JSON 对象
    - 包裹在 ```json ... ``` 中的 JSON

    Args:
        content: LLM 响应内容

    Returns:
        解析后的字典，解析失败返回 None
    """
    try:
        json_match = re.search(r"```json\s*(\{.*\})\s*```", content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = content

        json_str = json_str.strip()
        if not json_str.startswith("{"):
            json_match = re.search(r"\{.*\}", json_str, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)

        return json.loads(json_str)
    except (json.JSONDecodeError, AttributeError):
        return None
