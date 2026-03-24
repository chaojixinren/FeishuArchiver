"""
LangGraph 工作流定义

[INPUT]: 飞书文档 URL
[OUTPUT]: 归档后的项目信息（含评分和决策）
[POS]: 定义完整的工作流图结构
"""

from langgraph.graph import StateGraph, END

from src.graph.state import WorkflowState
from src.graph.nodes.parse_document import parse_document_node
from src.graph.nodes.extract_and_archive import extract_and_archive_node
from src.graph.nodes.score_and_decide import score_and_decide_node


def create_workflow() -> StateGraph:
    """
    创建工作流图

    Returns:
        编译后的工作流图
    """
    builder = StateGraph(WorkflowState)

    builder.add_node("parse_document", parse_document_node)
    builder.add_node("extract_and_archive", extract_and_archive_node)
    builder.add_node("score_and_decide", score_and_decide_node)

    builder.set_entry_point("parse_document")

    builder.add_edge("parse_document", "extract_and_archive")
    builder.add_edge("extract_and_archive", "score_and_decide")
    builder.add_edge("score_and_decide", END)

    return builder


def compile_workflow():
    """
    编译工作流

    Returns:
        可执行的工作流
    """
    builder = create_workflow()
    return builder.compile()


workflow = compile_workflow()
