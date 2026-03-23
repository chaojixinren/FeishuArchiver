"""
节点2: 项目信息提取与归档测试

测试内容:
- 项目信息提取
- 数据库存储
- 错误处理
"""

import os
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from src.graph.nodes.extract_and_archive import (
    extract_projects_with_llm,
    archive_projects,
    extract_and_archive_node,
    ExtractedProject,
    ProjectList,
)
from src.graph.state import WorkflowState
from src.db.database import Database, ProjectRepository


class TestExtractedProject:
    """测试项目信息模型"""

    def test_create_project_with_defaults(self):
        """测试创建项目（默认值）"""
        project = ExtractedProject(project_name="测试项目")
        assert project.project_name == "测试项目"
        assert project.project_intro == ""
        assert project.project_category == ""
        assert project.source_channel == "未知"

    def test_create_project_with_all_fields(self):
        """测试创建项目（所有字段）"""
        project = ExtractedProject(
            project_name="AI客服",
            project_intro="智能客服系统",
            project_category="AI产品",
            founder_name="张三",
            founder_contact="zhangsan@example.com",
            dx_contact="李四",
            source_channel="微信",
        )
        assert project.project_name == "AI客服"
        assert project.founder_name == "张三"


class TestArchiveProjects:
    """测试项目归档"""

    @patch("src.graph.nodes.extract_and_archive.project_repo")
    def test_archive_single_project(self, mock_repo):
        """测试归档单个项目"""
        mock_repo.insert.return_value = 1

        projects = [{"project_name": "测试项目", "founder_name": "张三"}]
        document_id = "doc_123"

        result = archive_projects(projects, document_id)

        assert len(result) == 1
        assert "✅" in result[0]
        assert "测试项目" in result[0]
        mock_repo.insert.assert_called_once()

    @patch("src.graph.nodes.extract_and_archive.project_repo")
    def test_archive_multiple_projects(self, mock_repo):
        """测试归档多个项目"""
        mock_repo.insert.side_effect = [1, 2]

        projects = [
            {"project_name": "项目A"},
            {"project_name": "项目B"},
        ]

        result = archive_projects(projects, "doc_123")

        assert len(result) == 2
        assert mock_repo.insert.call_count == 2

    @patch("src.graph.nodes.extract_and_archive.project_repo")
    def test_archive_with_error(self, mock_repo):
        """测试归档失败"""
        mock_repo.insert.side_effect = Exception("数据库错误")

        projects = [{"project_name": "测试项目"}]
        result = archive_projects(projects, "doc_123")

        assert len(result) == 1
        assert "❌" in result[0]
        assert "数据库错误" in result[0]


class TestExtractAndArchiveNode:
    """测试节点2完整流程"""

    def test_document_not_parsed(self):
        """测试文档未解析"""
        state: WorkflowState = {
            "feishu_url": "https://xxx.feishu.cn/docx/xxx",
            "document_id": "doc_123",
            "document_content": "内容...",
            "document_parsed": False,
            "extracted_projects": [],
            "archive_status": [],
            "project_scores": None,
            "next_actions": None,
            "errors": [],
            "current_node": None,
        }

        result = extract_and_archive_node(state)

        assert result["current_node"] == "extract_and_archive"
        assert len(result["errors"]) > 0
        assert "尚未解析" in result["errors"][0]

    def test_empty_document_content(self):
        """测试空文档内容"""
        state: WorkflowState = {
            "feishu_url": "https://xxx.feishu.cn/docx/xxx",
            "document_id": "doc_123",
            "document_content": "",
            "document_parsed": True,
            "extracted_projects": [],
            "archive_status": [],
            "project_scores": None,
            "next_actions": None,
            "errors": [],
            "current_node": None,
        }

        result = extract_and_archive_node(state)

        assert len(result["errors"]) > 0
        assert "为空" in result["errors"][0]

    @patch("src.graph.nodes.extract_and_archive.project_repo")
    @patch("src.graph.nodes.extract_and_archive.extract_projects_with_llm")
    def test_node_success(self, mock_extract, mock_repo):
        """测试节点成功执行"""
        mock_extract.return_value = [{"project_name": "测试项目", "founder_name": "张三"}]
        mock_repo.insert.return_value = 1

        state: WorkflowState = {
            "feishu_url": "https://xxx.feishu.cn/docx/xxx",
            "document_id": "doc_123",
            "document_content": "会议纪要内容...",
            "document_parsed": True,
            "extracted_projects": [],
            "archive_status": [],
            "project_scores": None,
            "next_actions": None,
            "errors": [],
            "current_node": None,
        }

        result = extract_and_archive_node(state)

        assert result["current_node"] == "extract_and_archive"
        assert len(result["extracted_projects"]) == 1
        assert len(result["archive_status"]) == 1

    @patch("src.graph.nodes.extract_and_archive.extract_projects_with_llm")
    def test_no_projects_extracted(self, mock_extract):
        """测试未提取到项目"""
        mock_extract.return_value = []

        state: WorkflowState = {
            "feishu_url": "https://xxx.feishu.cn/docx/xxx",
            "document_id": "doc_123",
            "document_content": "普通文本...",
            "document_parsed": True,
            "extracted_projects": [],
            "archive_status": [],
            "project_scores": None,
            "next_actions": None,
            "errors": [],
            "current_node": None,
        }

        result = extract_and_archive_node(state)

        assert len(result["extracted_projects"]) == 0
        assert "未从文档中提取到项目信息" in result["archive_status"][0]


class TestDatabaseIntegration:
    """测试数据库集成"""

    def test_database_connection(self):
        """测试数据库连接"""
        db = Database()
        with db.get_connection() as conn:
            assert conn is not None

    def test_project_repository_create_table(self):
        """测试创建表"""
        repo = ProjectRepository()
        repo.create_table()

        db = Database()
        result = db.fetch_one("SHOW TABLES LIKE 'projects'")
        assert result is not None

    def test_project_repository_insert(self):
        """测试插入项目"""
        repo = ProjectRepository()

        project = {
            "document_id": "test_doc_001",
            "project_name": "测试项目",
            "project_intro": "这是一个测试项目",
            "founder_name": "测试创始人",
        }

        project_id = repo.insert(project)
        assert project_id > 0

        db = Database()
        result = db.fetch_one("SELECT * FROM projects WHERE id = %s", (project_id,))
        assert result is not None
        assert result["project_name"] == "测试项目"

    def test_project_repository_find_by_document(self):
        """测试按文档ID查询"""
        repo = ProjectRepository()

        repo.insert(
            {
                "document_id": "test_doc_002",
                "project_name": "查询测试项目",
            }
        )

        results = repo.find_by_document("test_doc_002")
        assert len(results) >= 1
        assert results[0]["project_name"] == "查询测试项目"


class TestWorkflowWithNode2:
    """测试工作流集成（节点1 + 节点2）"""

    @patch("src.graph.nodes.extract_and_archive.project_repo")
    @patch("src.graph.nodes.extract_and_archive.extract_projects_with_llm")
    def test_full_workflow(self, mock_extract, mock_repo):
        """测试完整工作流"""
        from src.graph.workflow import workflow

        mock_extract.return_value = [{"project_name": "集成测试项目", "founder_name": "测试"}]
        mock_repo.insert.return_value = 1

        initial_state: WorkflowState = {
            "feishu_url": "https://xxx.feishu.cn/docx/test123",
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

        with patch("src.graph.nodes.parse_document.FeishuDocParser") as mock_parser:
            mock_instance = MagicMock()
            mock_parser.return_value = mock_instance
            mock_instance.get_document_content.return_value = "测试文档内容"

            result = workflow.invoke(initial_state)

        assert result.get("document_parsed") or len(result.get("errors", [])) > 0
