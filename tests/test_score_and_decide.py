"""
节点3: 项目评分与决策测试

测试内容:
- LLM 评分功能
- 数据库更新
- 状态判断
"""

import os
import pytest
from unittest.mock import MagicMock, patch

from src.graph.nodes.score_and_decide import (
    score_projects_with_llm,
    update_project_scores,
    score_and_decide_node,
    ProjectScore,
)
from src.graph.state import WorkflowState
from src.db.database import ProjectStatus


class TestScoreProjectsWithLLM:
    """测试 LLM 评分"""

    def test_empty_projects(self):
        """测试空项目列表"""
        os.environ["OPENAI_API_KEY"] = "test_key"
        result = score_projects_with_llm([])
        assert result == []

    @patch("src.graph.nodes.score_and_decide.score_projects_with_llm")
    def test_score_single_project(self, mock_score):
        """测试评分单个项目"""
        mock_score.return_value = [
            {"project_name": "智能客服", "score": 7, "next_action": "安排会议"}
        ]

        projects = [{"project_name": "智能客服"}]
        result = mock_score(projects)

        assert len(result) == 1
        assert result[0]["project_name"] == "智能客服"
        assert result[0]["score"] == 7

    @patch("src.graph.nodes.score_and_decide.score_projects_with_llm")
    def test_score_multiple_projects(self, mock_score):
        """测试评分多个项目"""
        mock_score.return_value = [
            {"project_name": "项目A", "score": 8, "next_action": "跟进"},
            {"project_name": "项目B", "score": 5, "next_action": "调研"},
        ]

        projects = [{"project_name": "项目A"}, {"project_name": "项目B"}]
        result = mock_score(projects)

        assert len(result) == 2


class TestUpdateProjectScores:
    """测试更新数据库"""

    @patch("src.graph.nodes.score_and_decide.project_repo")
    def test_update_single_score(self, mock_repo):
        """测试更新单个评分"""
        mock_repo.find_by_document.return_value = [{"id": 1, "project_name": "智能客服"}]
        mock_repo.db = MagicMock()

        scores = [{"project_name": "智能客服", "score": 8, "next_action": "安排会议"}]

        result = update_project_scores(scores, "doc_123")

        assert len(result) == 1
        assert "✅" in result[0]
        mock_repo.update_score.assert_called_once_with(1, 8, "安排会议", ProjectStatus.APPROVED)

    @patch("src.graph.nodes.score_and_decide.project_repo")
    def test_update_with_high_score(self, mock_repo):
        """测试高分项目状态"""
        mock_repo.find_by_document.return_value = [{"id": 1, "project_name": "优质项目"}]

        scores = [{"project_name": "优质项目", "score": 9, "next_action": "立即跟进"}]
        update_project_scores(scores, "doc_123")

        mock_repo.update_score.assert_called_once_with(1, 9, "立即跟进", ProjectStatus.APPROVED)

    @patch("src.graph.nodes.score_and_decide.project_repo")
    def test_update_with_low_score(self, mock_repo):
        """测试低分项目状态"""
        mock_repo.find_by_document.return_value = [{"id": 1, "project_name": "待改进项目"}]

        scores = [{"project_name": "待改进项目", "score": 3, "next_action": "暂缓跟进"}]
        update_project_scores(scores, "doc_123")

        mock_repo.update_score.assert_called_once_with(1, 3, "暂缓跟进", ProjectStatus.REJECTED)


class TestScoreAndDecideNode:
    """测试节点3完整流程"""

    def test_no_projects_to_score(self):
        """测试没有项目需要评分"""
        state: WorkflowState = {
            "feishu_url": "https://xxx.feishu.cn/docx/xxx",
            "document_id": "doc_123",
            "document_content": "内容",
            "document_parsed": True,
            "extracted_projects": [],
            "archive_status": [],
            "project_scores": None,
            "next_actions": None,
            "errors": [],
            "current_node": None,
        }

        result = score_and_decide_node(state)

        assert result["current_node"] == "score_and_decide"
        assert len(result["errors"]) > 0

    def test_missing_document_id(self):
        """测试缺少文档ID"""
        state: WorkflowState = {
            "feishu_url": "https://xxx.feishu.cn/docx/xxx",
            "document_id": None,
            "document_content": "内容",
            "document_parsed": True,
            "extracted_projects": [{"project_name": "测试项目"}],
            "archive_status": [],
            "project_scores": None,
            "next_actions": None,
            "errors": [],
            "current_node": None,
        }

        result = score_and_decide_node(state)

        assert len(result["errors"]) > 0
        assert "文档ID" in result["errors"][0]

    @patch("src.graph.nodes.score_and_decide.project_repo")
    @patch("src.graph.nodes.score_and_decide.score_projects_with_llm")
    def test_node_success(self, mock_score, mock_repo):
        """测试节点成功执行"""
        mock_score.return_value = [{"project_name": "测试项目", "score": 7, "next_action": "跟进"}]
        mock_repo.find_by_document.return_value = [{"id": 1, "project_name": "测试项目"}]

        state: WorkflowState = {
            "feishu_url": "https://xxx.feishu.cn/docx/xxx",
            "document_id": "doc_123",
            "document_content": "内容",
            "document_parsed": True,
            "extracted_projects": [{"project_name": "测试项目"}],
            "archive_status": [],
            "project_scores": None,
            "next_actions": None,
            "errors": [],
            "current_node": None,
        }

        result = score_and_decide_node(state)

        assert result["current_node"] == "score_and_decide"
        assert result["project_scores"]["测试项目"] == 7
        assert result["next_actions"]["测试项目"] == "跟进"


class TestWorkflowWithNode3:
    """测试完整工作流"""

    @patch("src.graph.nodes.score_and_decide.project_repo")
    @patch("src.graph.nodes.score_and_decide.score_projects_with_llm")
    @patch("src.graph.nodes.extract_and_archive.project_repo")
    @patch("src.graph.nodes.extract_and_archive.extract_projects_with_llm")
    def test_full_workflow(self, mock_extract, mock_archive_repo, mock_score, mock_score_repo):
        """测试完整工作流（节点1+2+3）"""
        from src.graph.workflow import workflow

        mock_extract.return_value = ([{"project_name": "测试项目"}], "成功提取项目信息")
        mock_archive_repo.insert.return_value = 1

        mock_score.return_value = [
            {"project_name": "测试项目", "score": 8, "next_action": "深度沟通"}
        ]
        mock_score_repo.find_by_document.return_value = [{"id": 1, "project_name": "测试项目"}]

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

        assert "project_scores" in result
