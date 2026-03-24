"""
节点3: 项目评分与决策

[INPUT]: 提取的项目信息列表
[OUTPUT]: 项目评分、评分理由、下一步动作
[POS]: 使用 LLM 智能评估项目并生成决策建议
"""

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from src.graph.state import WorkflowState
from src.db.database import project_repo, ProjectStatus
from src.llm import get_llm_client, parse_json_from_llm_response
from src.prompts import SCORING_PROMPT


class ProjectScore(BaseModel):
    """项目评分结果"""

    project_name: str = Field(description="项目名称")
    score: int = Field(ge=1, le=10, description="评分 1-10")
    reasoning: str = Field(description="评分理由")
    next_action: str = Field(description="建议的下一步动作")


class ScoreList(BaseModel):
    """评分列表"""

    scores: list[ProjectScore] = Field(default_factory=list)




def score_projects_with_llm(projects: list[dict]) -> list[dict]:
    """
    使用 LLM 对项目进行评分

    Args:
        projects: 项目信息列表

    Returns:
        评分结果列表
    """
    if not projects:
        return []

    project_info_lines = []
    for i, p in enumerate(projects, 1):
        project_info_lines.append(f"### 项目 {i}")
        project_info_lines.append(f"- 名称: {p.get('project_name', '未知')}")
        project_info_lines.append(f"- 简介: {p.get('project_intro', '无')}")
        project_info_lines.append(f"- 类别: {p.get('project_category', '未知')}")
        project_info_lines.append(f"- 创始人: {p.get('founder_name', '未知')}")
        project_info_lines.append(f"- 联系方式: {p.get('founder_contact', '无')}")
        project_info_lines.append(f"- DX对接人: {p.get('dx_contact', '无')}")
        project_info_lines.append("")

    project_info = "\n".join(project_info_lines)

    llm = get_llm_client()
    prompt = ChatPromptTemplate.from_template(SCORING_PROMPT)
    chain = prompt | llm

    response = chain.invoke({"project_info": project_info})
    data = parse_json_from_llm_response(response.content)

    return data.get("scores", []) if data else []


def update_project_scores(scores: list[dict], document_id: str) -> list[str]:
    """
    更新项目评分到数据库

    Args:
        scores: 评分结果列表
        document_id: 文档ID

    Returns:
        更新状态列表
    """
    status_list = []

    existing_projects = project_repo.find_by_document(document_id)
    name_to_id = {p["project_name"]: p["id"] for p in existing_projects}

    for score_data in scores:
        project_name = score_data.get("project_name", "")
        score = score_data.get("score", 0)
        next_action = score_data.get("next_action", "")

        project_id = name_to_id.get(project_name)

        if project_id:
            try:
                if score >= 8:
                    status = ProjectStatus.APPROVED
                elif score >= 5:
                    status = ProjectStatus.REVIEWED
                else:
                    status = ProjectStatus.REJECTED

                project_repo.update_score(project_id, score, next_action, status)
                status_list.append(
                    f"✅ '{project_name}' 评分: {score}/10 | 动作: {next_action[:30]}..."
                )
            except Exception as e:
                status_list.append(f"❌ '{project_name}' 更新失败: {str(e)}")
        else:
            status_list.append(f"⚠️  '{project_name}' 未在数据库中找到")

    return status_list


def score_and_decide_node(state: WorkflowState) -> dict:
    """
    节点3: 项目评分与决策

    对提取的项目进行智能评分，生成下一步动作建议

    Args:
        state: 当前工作流状态

    Returns:
        状态更新字典
    """
    projects = state.get("extracted_projects", [])
    document_id = state.get("document_id", "")

    if not projects:
        return {
            "project_scores": {},
            "next_actions": {},
            "errors": ["错误: 没有项目需要评分"],
            "current_node": "score_and_decide",
        }

    if not document_id:
        return {
            "project_scores": {},
            "next_actions": {},
            "errors": ["错误: 缺少文档ID"],
            "current_node": "score_and_decide",
        }

    try:
        scores = score_projects_with_llm(projects)

        if not scores:
            return {
                "project_scores": {},
                "next_actions": {},
                "errors": ["错误: 未能生成评分结果"],
                "current_node": "score_and_decide",
            }

        status_list = update_project_scores(scores, document_id)

        project_scores = {s["project_name"]: s["score"] for s in scores}
        next_actions = {s["project_name"]: s["next_action"] for s in scores}

        return {
            "project_scores": project_scores,
            "next_actions": next_actions,
            "archive_status": status_list,
            "current_node": "score_and_decide",
        }

    except Exception as e:
        error_msg = f"评分失败: {str(e)}"
        return {
            "project_scores": {},
            "next_actions": {},
            "errors": [error_msg],
            "current_node": "score_and_decide",
        }
