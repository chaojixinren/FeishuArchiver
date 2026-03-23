"""
测试配置和 fixtures
"""

import os
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def setup_env():
    """设置测试环境变量"""
    os.environ["FEISHU_APP_ID"] = "cli_test_app_id"
    os.environ["FEISHU_APP_SECRET"] = "test_app_secret"
    yield
    # 清理
    if "FEISHU_APP_ID" in os.environ:
        del os.environ["FEISHU_APP_ID"]
    if "FEISHU_APP_SECRET" in os.environ:
        del os.environ["FEISHU_APP_SECRET"]


@pytest.fixture
def mock_feishu_exporter():
    """Mock FeishuExporter"""
    with patch("src.graph.nodes.parse_document.FeishuExporter") as mock:
        yield mock


@pytest.fixture
def sample_docx_url():
    """示例 docx 文档 URL"""
    return "https://pcnsewcvcu2i.feishu.cn/docx/UxdAdOyw2oWAs8x5voKcghGjnhh"


@pytest.fixture
def sample_wiki_url():
    """示例 wiki URL"""
    return "https://open.feishu.cn/wiki/UxdAdOyw2oWAs8x5voKcghGjnhh"


@pytest.fixture
def sample_minutes_url():
    """示例妙记 URL"""
    return "https://feishu.cn/minutes/==abc123=="


@pytest.fixture
def sample_document_content():
    """示例文档内容"""
    return """# 项目会议纪要

## 项目信息
- 项目名称：智能客服系统
- 项目类别：AI产品
- 创始人：张三
- DX对接人：李四

## 会议内容
本次会议讨论了项目的整体架构和下一步计划...

## 下一步动作
1. 安排技术评审会议
2. 准备 Demo 演示
"""


@pytest.fixture
def initial_state():
    """初始工作流状态"""
    from src.graph.state import WorkflowState

    return {
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
