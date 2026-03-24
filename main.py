#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Delta X 项目归档工作流 - 主入口

使用方法:
    # 单个 URL
    python main.py --url "https://xxx.feishu.cn/docx/xxx"

    # 多个 URL (并发处理)
    python main.py --url "https://xxx.feishu.cn/docx/xxx" "https://yyy.feishu.cn/docx/yyy"

    # 从文件读取 URL
    python main.py --url-file urls.txt

    # 详细输出
    python main.py --url "https://xxx.feishu.cn/docx/xxx" --verbose
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

from src.graph.workflow import workflow
from src.graph.state import WorkflowState


@dataclass
class ProcessResult:
    url: str
    success: bool
    document_id: Optional[str]
    projects_count: int
    archived_count: int
    errors: list[str]


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


def process_single_url(url: str) -> ProcessResult:
    """
    处理单个 URL，返回结构化结果

    Args:
        url: 飞书文档链接

    Returns:
        处理结果
    """
    result = run_workflow(url)

    projects = result.get("extracted_projects", [])
    archive_status = result.get("archive_status", [])
    errors = result.get("errors", [])

    archived_count = sum(1 for s in archive_status if s.startswith("✅"))

    return ProcessResult(
        url=url,
        success=result.get("document_parsed", False) and len(errors) == 0,
        document_id=result.get("document_id"),
        projects_count=len(projects),
        archived_count=archived_count,
        errors=errors,
    )


def run_workflows_parallel(urls: list[str], max_workers: int = 5) -> list[ProcessResult]:
    """
    并发处理多个 URL

    Args:
        urls: 飞书文档链接列表
        max_workers: 最大并发数

    Returns:
        处理结果列表
    """
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(process_single_url, url): url for url in urls}

        for future in as_completed(future_to_url):
            result = future.result()
            results.append(result)

    return results


def print_single_result(result: dict, verbose: bool = False):
    """打印单个文档的处理结果"""
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

    project_scores = result.get("project_scores", {})
    next_actions = result.get("next_actions", {})

    if project_scores:
        print("-" * 50)
        print("📊 项目评分:")
        for name, score in project_scores.items():
            action = next_actions.get(name, "")
            print(f"   {name}: {score}/10")
            print(f"      下一步: {action}")

    errors = result.get("errors", [])
    if errors:
        print("-" * 50)
        print("⚠️  错误信息:")
        for error in errors:
            print(f"   {error}")

    if verbose and result.get("document_content"):
        print("-" * 50)
        print("📄 文档内容预览:")
        content = result.get("document_content", "")
        print(content[:800] + "..." if len(content) > 800 else content)


def print_summary(results: list[ProcessResult]):
    """打印汇总结果"""
    print("\n" + "=" * 60)
    print("📊 处理汇总")
    print("=" * 60)

    total = len(results)
    success = sum(1 for r in results if r.success)
    failed = total - success
    total_projects = sum(r.projects_count for r in results)
    total_archived = sum(r.archived_count for r in results)

    print(f"📄 处理文档: {total} 个")
    print(f"✅ 成功: {success} 个")
    print(f"❌ 失败: {failed} 个")
    print(f"📋 提取项目: {total_projects} 个")
    print(f"💾 归档成功: {total_archived} 个")

    if failed > 0:
        print("\n⚠️  失败的文档:")
        for r in results:
            if not r.success:
                print(f"   - {r.url}")
                for err in r.errors[:2]:
                    print(f"     {err[:80]}...")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Delta X 项目归档工作流",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 单个 URL
  python main.py --url "https://xxx.feishu.cn/docx/xxx"
  
  # 多个 URL (并发处理)
  python main.py --url "https://xxx.feishu.cn/docx/xxx" "https://yyy.feishu.cn/docx/yyy"
  
  # 从文件读取 URL (每行一个)
  python main.py --url-file urls.txt
        """,
    )
    parser.add_argument(
        "--url",
        type=str,
        nargs="+",
        help="飞书文档链接 (支持多个)",
    )
    parser.add_argument(
        "--url-file",
        type=str,
        help="包含 URL 列表的文件路径 (每行一个)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=5,
        help="并发数 (默认: 5)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="显示详细输出",
    )

    args = parser.parse_args()

    urls = []
    if args.url:
        urls.extend(args.url)
    if args.url_file:
        with open(args.url_file, "r", encoding="utf-8") as f:
            urls.extend(line.strip() for line in f if line.strip())

    if not urls:
        parser.error("请提供至少一个 URL (--url 或 --url-file)")

    unique_urls = list(dict.fromkeys(urls))

    if len(unique_urls) == 1:
        print(f"正在处理文档: {unique_urls[0]}")
        print("-" * 50)
        result = run_workflow(unique_urls[0])
        print_single_result(result, args.verbose)
        return result

    print(f"🚀 开始并发处理 {len(unique_urls)} 个文档 (并发数: {args.workers})")
    print("-" * 50)

    results = run_workflows_parallel(unique_urls, max_workers=args.workers)

    for i, r in enumerate(results, 1):
        status = "✅" if r.success else "❌"
        print(
            f"{status} [{i}/{len(urls)}] {r.url[:50]}... | 项目: {r.projects_count} | 归档: {r.archived_count}"
        )
        if r.errors and args.verbose:
            for err in r.errors[:1]:
                print(f"      错误: {err[:60]}...")

    print_summary(results)
    return results


if __name__ == "__main__":
    main()
