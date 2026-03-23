#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Delta X 项目归档工作流 - 主入口

使用方法:
    python main.py --url "https://xxx.feishu.cn/docx/xxx"
    python main.py --url "https://xxx.feishu.cn/docx/xxx" --verbose
"""

import argparse
from dotenv import load_dotenv

load_dotenv()

from src.graph.workflow import workflow
from src.graph.state import WorkflowState


def run_workflow(url: str) -> dict:
    """
    运行工作流

    Args:
        url: 飞书文档链接

    Returns:
        工作流执行结果
    """
    initial_state: WorkflowState = {
        "feishu_url": url,
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

    result = workflow.invoke(initial_state)
    return result


def main():
    parser = argparse.ArgumentParser(description="Delta X 项目归档工作流")
    parser.add_argument("--url", type=str, required=True, help="飞书文档链接")
    parser.add_argument("--verbose", action="store_true", help="显示详细输出")

    args = parser.parse_args()

    print(f"正在处理文档: {args.url}")
    print("-" * 50)

    result = run_workflow(args.url)

    if result.get("document_parsed"):
        print("✅ 文档解析成功!")
        print(f"   文档ID: {result.get('document_id')}")
        print(f"   内容长度: {len(result.get('document_content', ''))} 字符")
    else:
        print("❌ 文档解析失败!")

    print("-" * 50)

    projects = result.get("extracted_projects", [])
    archive_status = result.get("archive_status", [])

    if projects:
        print(f"📋 提取到 {len(projects)} 个项目:")
        for i, project in enumerate(projects, 1):
            print(f"   {i}. {project.get('project_name', '未知项目')}")
            if project.get("founder_name"):
                print(f"      创始人: {project.get('founder_name')}")
    else:
        print("📋 未提取到项目信息")

    print("-" * 50)

    if archive_status:
        print("📁 归档状态:")
        for status in archive_status:
            print(f"   {status}")

    errors = result.get("errors", [])
    if errors:
        print("-" * 50)
        print("⚠️  错误信息:")
        for error in errors:
            print(f"   {error}")

    if args.verbose and result.get("document_content"):
        print("-" * 50)
        print("📄 文档内容预览:")
        content = result.get("document_content", "")
        print(content[:800] + "..." if len(content) > 800 else content)

    return result


if __name__ == "__main__":
    main()
