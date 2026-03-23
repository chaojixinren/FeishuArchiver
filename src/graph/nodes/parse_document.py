"""
节点1: 文档解析节点

[INPUT]: 飞书文档 URL
[OUTPUT]: 文档内容（Markdown格式）
[POS]: 使用飞书 API 解析飞书文档
"""

import re
import os
from typing import Optional
import httpx

from src.graph.state import WorkflowState


class FeishuDocParser:
    """飞书文档解析器"""

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self._token: Optional[str] = None

    def _get_token(self) -> str:
        """获取 tenant_access_token"""
        if self._token:
            return self._token

        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        data = {"app_id": self.app_id, "app_secret": self.app_secret}

        response = httpx.post(url, json=data)
        result = response.json()

        if result.get("code") != 0:
            raise RuntimeError(f"获取 Token 失败: {result.get('msg')}")

        self._token = result.get("tenant_access_token")
        return self._token

    def get_document_content(self, document_id: str) -> str:
        """
        获取文档内容并转换为 Markdown

        Args:
            document_id: 文档 ID

        Returns:
            Markdown 格式的文档内容
        """
        token = self._get_token()

        url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{document_id}/blocks"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        response = httpx.get(url, headers=headers)
        result = response.json()

        if result.get("code") != 0:
            raise RuntimeError(f"获取文档失败: {result.get('msg')}")

        blocks = result.get("data", {}).get("items", [])
        return self._blocks_to_markdown(blocks)

    def _blocks_to_markdown(self, blocks: list) -> str:
        """将 blocks 转换为 Markdown"""
        lines = []

        for block in blocks:
            block_type = block.get("block_type")

            if block_type == 2:  # Text
                text = self._extract_text(block.get("text", {}))
                if text:
                    lines.append(text)

            elif block_type == 3:  # Heading1
                text = self._extract_text(block.get("heading1", {}))
                if text:
                    lines.append(f"# {text}")

            elif block_type == 4:  # Heading2
                text = self._extract_text(block.get("heading2", {}))
                if text:
                    lines.append(f"## {text}")

            elif block_type == 5:  # Heading3
                text = self._extract_text(block.get("heading3", {}))
                if text:
                    lines.append(f"### {text}")

            elif block_type == 6:  # Heading4
                text = self._extract_text(block.get("heading4", {}))
                if text:
                    lines.append(f"#### {text}")

            elif block_type == 7:  # Heading5
                text = self._extract_text(block.get("heading5", {}))
                if text:
                    lines.append(f"##### {text}")

            elif block_type == 8:  # Heading6
                text = self._extract_text(block.get("heading6", {}))
                if text:
                    lines.append(f"###### {text}")

            elif block_type == 12:  # Bullet (无序列表)
                text = self._extract_text(block.get("bullet", {}))
                if text:
                    lines.append(f"- {text}")

            elif block_type == 13:  # Ordered (有序列表)
                text = self._extract_text(block.get("ordered", {}))
                if text:
                    lines.append(f"1. {text}")

            elif block_type == 14:  # Code
                text = self._extract_text(block.get("code", {}))
                if text:
                    lines.append(f"```\n{text}\n```")

            elif block_type == 15:  # Quote
                text = self._extract_text(block.get("quote", {}))
                if text:
                    lines.append(f"> {text}")

        return "\n\n".join(lines)

    def _extract_text(self, block_data: dict) -> str:
        """从 block 数据中提取文本"""
        elements = block_data.get("elements", [])
        texts = []

        for elem in elements:
            if "text_run" in elem:
                texts.append(elem["text_run"].get("content", ""))

        return "".join(texts)


def parse_feishu_url(url: str) -> Optional[dict]:
    """
    解析飞书文档 URL，提取文档类型和 ID

    Args:
        url: 飞书文档链接

    Returns:
        {"type": "docx", "token": "xxx"} 或 None
    """
    patterns = {
        "docx": re.compile(
            r"(?:feishu|larksuite)\.cn/docx/([a-zA-Z0-9]+)|larkoffice\.com/docx/([a-zA-Z0-9]+)"
        ),
        "doc": re.compile(
            r"(?:feishu|larksuite)\.cn/doc/([a-zA-Z0-9]+)|larkoffice\.com/doc/([a-zA-Z0-9]+)"
        ),
        "wiki": re.compile(
            r"(?:feishu|larksuite)\.cn/wiki/([a-zA-Z0-9]+)|larkoffice\.com/wiki/([a-zA-Z0-9]+)"
        ),
        "minutes": re.compile(
            r"(?:feishu|larksuite)\.cn/minutes/==([a-zA-Z0-9]+)==|larkoffice\.com/minutes/==([a-zA-Z0-9]+)=="
        ),
    }

    for doc_type, pattern in patterns.items():
        match = pattern.search(url)
        if match:
            token = match.group(1) or match.group(2)
            return {"type": doc_type, "token": token}

    return None


def parse_document_node(state: WorkflowState) -> dict:
    """
    节点1: 解析飞书文档

    从 URL 获取文档内容，转换为 Markdown 格式

    Args:
        state: 当前工作流状态

    Returns:
        状态更新字典
    """
    url = state.get("feishu_url", "")

    if not url:
        return {
            "document_parsed": False,
            "errors": ["错误: 未提供飞书文档链接"],
            "current_node": "parse_document",
        }

    url_info = parse_feishu_url(url)
    if not url_info:
        return {
            "document_parsed": False,
            "errors": [f"错误: 无法解析飞书文档链接格式: {url}"],
            "current_node": "parse_document",
        }

    doc_type = url_info["type"]
    doc_token = url_info["token"]

    if doc_type == "minutes":
        return {
            "document_id": doc_token,
            "document_parsed": False,
            "errors": ["注意: 检测到妙记链接，当前版本暂不支持妙记解析，请提供普通云文档链接"],
            "current_node": "parse_document",
        }

    try:
        app_id = os.getenv("FEISHU_APP_ID")
        app_secret = os.getenv("FEISHU_APP_SECRET")

        if not app_id or not app_secret:
            return {
                "document_parsed": False,
                "errors": [
                    "错误: 未配置飞书应用凭证，请设置 FEISHU_APP_ID 和 FEISHU_APP_SECRET 环境变量"
                ],
                "current_node": "parse_document",
            }

        parser = FeishuDocParser(app_id=app_id, app_secret=app_secret)
        content = parser.get_document_content(doc_token)

        if not content:
            return {
                "document_id": doc_token,
                "document_parsed": False,
                "errors": ["错误: 文档内容为空"],
                "current_node": "parse_document",
            }

        return {
            "document_id": doc_token,
            "document_content": content,
            "document_parsed": True,
            "current_node": "parse_document",
        }

    except Exception as e:
        error_msg = f"解析文档失败: {str(e)}"
        return {
            "document_id": doc_token,
            "document_parsed": False,
            "errors": [error_msg],
            "current_node": "parse_document",
        }
