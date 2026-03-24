"""
节点2: 项目信息提取与归档

[INPUT]: 文档内容（Markdown格式）
[OUTPUT]: 提取的项目信息列表，存储到 MySQL
[POS]: 使用 LLM 提取项目信息，存入数据库
"""

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from src.graph.state import WorkflowState
from src.db.database import project_repo
from src.llm import get_llm_client, parse_json_from_llm_response
from src.prompts import EXTRACTION_PROMPT


class ExtractedProject(BaseModel):
    """提取的项目信息"""

    project_name: str = Field(description="项目名称")
    project_intro: str = Field(default="", description="项目简介")
    project_category: str = Field(default="", description="项目类别，如：AI产品、SaaS、硬件等")
    founder_name: str = Field(default="", description="创始人或负责人姓名")
    founder_contact: str = Field(default="", description="创始人联系方式（电话、微信、邮箱等）")
    dx_contact: str = Field(default="", description="DX对接人姓名")
    source_channel: str = Field(default="未知", description="来源渠道，如：微信、企微、活动现场等")


class ProjectList(BaseModel):
    """项目列表"""

    projects: list[ExtractedProject] = Field(default_factory=list, description="提取的项目列表")




def extract_projects_with_llm(document_content: str) -> list[dict]:
    """
    使用 LLM 从文档中提取项目信息

    Args:
        document_content: 文档内容（Markdown格式）

    Returns:
        提取的项目信息列表
    """
    llm = get_llm_client()
    prompt = ChatPromptTemplate.from_template(EXTRACTION_PROMPT)
    chain = prompt | llm

    response = chain.invoke({"document_content": document_content})
    data = parse_json_from_llm_response(response.content)

    return data.get("projects", []) if data else []


def archive_projects(projects: list[dict], document_id: str) -> list[str]:
    """
    将项目信息存入数据库

    Args:
        projects: 项目信息列表
        document_id: 文档ID

    Returns:
        归档状态列表
    """
    status_list = []

    for project in projects:
        try:
            project["document_id"] = document_id

            project_id = project_repo.insert(project)
            status_list.append(
                f"✅ 项目 '{project.get('project_name', '未知')}' 已归档，ID: {project_id}"
            )
        except Exception as e:
            status_list.append(
                f"❌ 项目 '{project.get('project_name', '未知')}' 归档失败: {str(e)}"
            )

    return status_list


def extract_and_archive_node(state: WorkflowState) -> dict:
    """
    节点2: 提取项目信息并归档

    从文档内容中提取项目信息，存入 MySQL 数据库

    Args:
        state: 当前工作流状态

    Returns:
        状态更新字典
    """
    document_content = state.get("document_content", "")
    document_id = state.get("document_id", "")
    document_parsed = state.get("document_parsed", False)

    if not document_parsed:
        return {
            "errors": ["错误: 文档尚未解析，无法提取项目信息"],
            "current_node": "extract_and_archive",
        }

    if not document_content:
        return {
            "errors": ["错误: 文档内容为空，无法提取项目信息"],
            "current_node": "extract_and_archive",
        }

    try:
        projects = extract_projects_with_llm(document_content)

        if not projects:
            return {
                "extracted_projects": [],
                "archive_status": ["提示: 未从文档中提取到项目信息"],
                "current_node": "extract_and_archive",
            }

        status_list = archive_projects(projects, document_id)

        return {
            "extracted_projects": projects,
            "archive_status": status_list,
            "current_node": "extract_and_archive",
        }

    except Exception as e:
        error_msg = f"提取项目信息失败: {str(e)}"
        return {
            "errors": [error_msg],
            "current_node": "extract_and_archive",
        }
