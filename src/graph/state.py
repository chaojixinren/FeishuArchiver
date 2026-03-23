"""
工作流状态定义

[INPUT]: 工作流节点间传递的数据结构
[OUTPUT]: TypedDict 定义的状态类
[POS]: 定义整个工作流的数据流转格式
"""

from typing import Annotated, TypedDict, Optional


def append_list(current: list, new: list) -> list:
    """列表合并 reducer"""
    return current + new


class ProjectInfo(TypedDict):
    """项目信息结构"""

    project_name: str  # 项目名称
    project_intro: str  # 项目简介
    project_category: str  # 项目类别
    founder_name: str  # 创始人姓名
    founder_contact: str  # 创始人联系方式
    dx_contact: str  # DX对接人
    source_channel: str  # 来源渠道


class WorkflowState(TypedDict):
    """
    工作流状态

    节点间通过此状态传递数据，每个节点返回部分状态更新
    """

    # === 节点1: 文档解析 ===
    feishu_url: str  # 输入：飞书文档链接
    document_id: Optional[str]  # 解析出的文档ID
    document_content: Optional[str]  # 文档内容（Markdown格式）
    document_parsed: bool  # 解析是否成功

    # === 节点2: 提取归档 ===
    extracted_projects: Annotated[list[ProjectInfo], append_list]  # 提取的项目列表
    archive_status: Annotated[list[str], append_list]  # 归档状态记录

    # === 节点3: 打分决策 ===
    project_scores: Optional[dict[str, int]]  # 项目评分 {project_name: score}
    next_actions: Optional[dict[str, str]]  # 下一步动作 {project_name: action}

    # === 错误处理 ===
    errors: Annotated[list[str], append_list]  # 错误信息
    current_node: Optional[str]  # 当前执行的节点
