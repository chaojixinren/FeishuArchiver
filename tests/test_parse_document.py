"""
节点1: 文档解析节点测试

测试内容:
- URL 解析功能
- 文档获取功能
- 错误处理
"""

import os
import pytest
from unittest.mock import MagicMock, patch

from src.graph.nodes.parse_document import (
    parse_feishu_url,
    parse_document_node,
    FeishuDocParser,
)
from src.graph.state import WorkflowState


class TestParseFeishuUrl:
    """测试 URL 解析功能"""

    def test_parse_docx_url(self):
        """测试标准 docx URL"""
        url = "https://pcnsewcvcu2i.feishu.cn/docx/UxdAdOyw2oWAs8x5voKcghGjnhh"
        result = parse_feishu_url(url)

        assert result is not None
        assert result["type"] == "docx"
        assert result["token"] == "UxdAdOyw2oWAs8x5voKcghGjnhh"

    def test_parse_docx_url_with_larksuite(self):
        """测试 larksuite 域名的 docx URL"""
        url = "https://open.larksuite.cn/docx/Abc123Xyz789"
        result = parse_feishu_url(url)

        assert result is not None
        assert result["type"] == "docx"
        assert result["token"] == "Abc123Xyz789"

    def test_parse_old_doc_url(self):
        """测试旧版 doc URL"""
        url = "https://open.feishu.cn/doc/UxdAdOyw2oWAs8x5voKcghGjnhh"
        result = parse_feishu_url(url)

        assert result is not None
        assert result["type"] == "doc"
        assert result["token"] == "UxdAdOyw2oWAs8x5voKcghGjnhh"

    def test_parse_wiki_url(self):
        """测试 wiki URL"""
        url = "https://open.feishu.cn/wiki/UxdAdOyw2oWAs8x5voKcghGjnhh"
        result = parse_feishu_url(url)

        assert result is not None
        assert result["type"] == "wiki"
        assert result["token"] == "UxdAdOyw2oWAs8x5voKcghGjnhh"

    def test_parse_minutes_url(self):
        """测试妙记 URL"""
        url = "https://feishu.cn/minutes/==abc123=="
        result = parse_feishu_url(url)

        assert result is not None
        assert result["type"] == "minutes"
        assert result["token"] == "abc123"

    def test_parse_minutes_url_with_larksuite(self):
        """测试 larksuite 域名的妙记 URL"""
        url = "https://open.larksuite.cn/minutes/==xyz789=="
        result = parse_feishu_url(url)

        assert result is not None
        assert result["type"] == "minutes"
        assert result["token"] == "xyz789"

    def test_parse_invalid_url(self):
        """测试无效 URL"""
        invalid_urls = [
            "https://google.com",
            "not a url",
            "",
            "https://feishu.cn/unknown/abc123",
        ]

        for url in invalid_urls:
            result = parse_feishu_url(url)
            assert result is None, f"URL '{url}' should return None"

    def test_parse_url_with_query_params(self):
        """测试带查询参数的 URL"""
        url = "https://pcnsewcvcu2i.feishu.cn/docx/UxdAdOyw2oWAs8x5voKcghGjnhh?from=from_copylink"
        result = parse_feishu_url(url)

        assert result is not None
        assert result["type"] == "docx"
        assert result["token"] == "UxdAdOyw2oWAs8x5voKcghGjnhh"


class TestFeishuDocParser:
    """测试飞书文档解析器"""

    def test_extract_text(self):
        """测试文本提取"""
        parser = FeishuDocParser("test_app_id", "test_secret")

        block_data = {
            "elements": [
                {"text_run": {"content": "Hello "}},
                {"text_run": {"content": "World"}},
            ]
        }

        text = parser._extract_text(block_data)
        assert text == "Hello World"

    def test_blocks_to_markdown_heading(self):
        """测试标题转换"""
        parser = FeishuDocParser("test_app_id", "test_secret")

        blocks = [
            {
                "block_type": 3,
                "heading1": {"elements": [{"text_run": {"content": "Title1"}}]},
            },
            {
                "block_type": 4,
                "heading2": {"elements": [{"text_run": {"content": "Title2"}}]},
            },
        ]

        markdown = parser._blocks_to_markdown(blocks)
        assert "# Title1" in markdown
        assert "## Title2" in markdown

    def test_blocks_to_markdown_text(self):
        """测试普通文本转换"""
        parser = FeishuDocParser("test_app_id", "test_secret")

        blocks = [
            {
                "block_type": 2,
                "text": {"elements": [{"text_run": {"content": "Normal text"}}]},
            },
        ]

        markdown = parser._blocks_to_markdown(blocks)
        assert "Normal text" in markdown


class TestParseDocumentNode:
    """测试文档解析节点"""

    def test_parse_document_empty_url(self):
        """测试空 URL"""
        state: WorkflowState = {
            "feishu_url": "",
            "document_id": None,
            "document_content": None,
            "document_parsed": False,
            "extracted_projects": [],
            "archive_status": [],
            "project_scores": None,
            "next_actions": None,
            "errors": [],
            "current_node": None,
        }

        result = parse_document_node(state)

        assert result["document_parsed"] is False
        assert len(result["errors"]) > 0
        assert "未提供飞书文档链接" in result["errors"][0]

    def test_parse_document_invalid_url(self):
        """测试无效 URL"""
        state: WorkflowState = {
            "feishu_url": "https://google.com",
            "document_id": None,
            "document_content": None,
            "document_parsed": False,
            "extracted_projects": [],
            "archive_status": [],
            "project_scores": None,
            "next_actions": None,
            "errors": [],
            "current_node": None,
        }

        result = parse_document_node(state)

        assert result["document_parsed"] is False
        assert len(result["errors"]) > 0
        assert "无法解析" in result["errors"][0]

    def test_parse_document_minutes_not_supported(self):
        """测试妙记链接暂不支持"""
        state: WorkflowState = {
            "feishu_url": "https://feishu.cn/minutes/==abc123==",
            "document_id": None,
            "document_content": None,
            "document_parsed": False,
            "extracted_projects": [],
            "archive_status": [],
            "project_scores": None,
            "next_actions": None,
            "errors": [],
            "current_node": None,
        }

        result = parse_document_node(state)

        assert result["document_parsed"] is False
        assert "妙记" in result["errors"][0] or "暂不支持" in result["errors"][0]
        assert result["document_id"] == "abc123"

    def test_parse_document_missing_credentials(self):
        """测试缺少飞书凭证"""
        old_app_id = os.environ.pop("FEISHU_APP_ID", None)
        old_app_secret = os.environ.pop("FEISHU_APP_SECRET", None)

        state: WorkflowState = {
            "feishu_url": "https://pcnsewcvcu2i.feishu.cn/docx/UxdAdOyw2oWAs8x5voKcghGjnhh",
            "document_id": None,
            "document_content": None,
            "document_parsed": False,
            "extracted_projects": [],
            "archive_status": [],
            "project_scores": None,
            "next_actions": None,
            "errors": [],
            "current_node": None,
        }

        result = parse_document_node(state)

        assert result["document_parsed"] is False
        assert any("凭证" in e or "FEISHU" in e for e in result["errors"])

        if old_app_id:
            os.environ["FEISHU_APP_ID"] = old_app_id
        if old_app_secret:
            os.environ["FEISHU_APP_SECRET"] = old_app_secret

    @patch("src.graph.nodes.parse_document.FeishuDocParser")
    def test_parse_document_success(self, mock_parser_class):
        """测试成功解析文档"""
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        mock_parser.get_document_content.return_value = "# Test Document\n\nContent..."

        state: WorkflowState = {
            "feishu_url": "https://pcnsewcvcu2i.feishu.cn/docx/UxdAdOyw2oWAs8x5voKcghGjnhh",
            "document_id": None,
            "document_content": None,
            "document_parsed": False,
            "extracted_projects": [],
            "archive_status": [],
            "project_scores": None,
            "next_actions": None,
            "errors": [],
            "current_node": None,
        }

        result = parse_document_node(state)

        assert result["document_parsed"] is True
        assert result["document_id"] == "UxdAdOyw2oWAs8x5voKcghGjnhh"
        assert result["document_content"] == "# Test Document\n\nContent..."

    @patch("src.graph.nodes.parse_document.FeishuDocParser")
    def test_parse_document_empty_content(self, mock_parser_class):
        """测试文档内容为空"""
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        mock_parser.get_document_content.return_value = ""

        state: WorkflowState = {
            "feishu_url": "https://pcnsewcvcu2i.feishu.cn/docx/UxdAdOyw2oWAs8x5voKcghGjnhh",
            "document_id": None,
            "document_content": None,
            "document_parsed": False,
            "extracted_projects": [],
            "archive_status": [],
            "project_scores": None,
            "next_actions": None,
            "errors": [],
            "current_node": None,
        }

        result = parse_document_node(state)

        assert result["document_parsed"] is False
        assert "空" in result["errors"][0]

    @patch("src.graph.nodes.parse_document.FeishuDocParser")
    def test_parse_document_api_error(self, mock_parser_class):
        """测试 API 调用失败"""
        mock_parser_class.side_effect = Exception("API Error: Permission denied")

        state: WorkflowState = {
            "feishu_url": "https://pcnsewcvcu2i.feishu.cn/docx/UxdAdOyw2oWAs8x5voKcghGjnhh",
            "document_id": None,
            "document_content": None,
            "document_parsed": False,
            "extracted_projects": [],
            "archive_status": [],
            "project_scores": None,
            "next_actions": None,
            "errors": [],
            "current_node": None,
        }

        result = parse_document_node(state)

        assert result["document_parsed"] is False
        assert "解析文档失败" in result["errors"][0]


class TestWorkflowIntegration:
    """测试工作流集成"""

    def test_state_immutability(self):
        """测试状态不可变性"""
        state: WorkflowState = {
            "feishu_url": "https://google.com",
            "document_id": None,
            "document_content": None,
            "document_parsed": False,
            "extracted_projects": [],
            "archive_status": [],
            "project_scores": None,
            "next_actions": None,
            "errors": [],
            "current_node": None,
        }

        result = parse_document_node(state)

        assert result is not None
        assert isinstance(result, dict)

    def test_current_node_tracking(self):
        """测试当前节点追踪"""
        state: WorkflowState = {
            "feishu_url": "",
            "document_id": None,
            "document_content": None,
            "document_parsed": False,
            "extracted_projects": [],
            "archive_status": [],
            "project_scores": None,
            "next_actions": None,
            "errors": [],
            "current_node": None,
        }

        result = parse_document_node(state)

        assert result["current_node"] == "parse_document"


class TestEdgeCases:
    """边界条件测试"""

    def test_url_with_special_characters(self):
        """测试包含特殊字符的 URL"""
        url = "https://open.feishu.cn/docx/UxdAdOyw2oWAs8x5voKcghGjnhh?title=test"
        result = parse_feishu_url(url)

        assert result is not None
        assert result["token"] == "UxdAdOyw2oWAs8x5voKcghGjnhh"

    def test_url_with_fragment(self):
        """测试带有锚点的 URL"""
        url = "https://open.feishu.cn/docx/UxdAdOyw2oWAs8x5voKcghGjnhh#heading-1"
        result = parse_feishu_url(url)

        assert result is not None
        assert result["token"] == "UxdAdOyw2oWAs8x5voKcghGjnhh"

    def test_url_case_sensitivity(self):
        """测试 URL 大小写"""
        url1 = "https://open.feishu.cn/docx/ABC123"
        url2 = "https://open.feishu.cn/docx/abc123"

        result1 = parse_feishu_url(url1)
        result2 = parse_feishu_url(url2)

        assert result1["token"] != result2["token"]

    def test_multiple_errors_accumulation(self):
        """测试错误累积"""
        state: WorkflowState = {
            "feishu_url": "",
            "document_id": None,
            "document_content": None,
            "document_parsed": False,
            "extracted_projects": [],
            "archive_status": [],
            "project_scores": None,
            "next_actions": None,
            "errors": ["Existing error"],
            "current_node": None,
        }

        result = parse_document_node(state)

        assert len(result["errors"]) >= 1
