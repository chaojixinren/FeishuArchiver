#!/usr/bin/env python3
"""
清理数据库脚本

用法:
    python scripts/clean_db.py           # 清空 projects 表
    python scripts/clean_db.py --force   # 跳过确认
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.database import db


def clean_projects(force: bool = False) -> None:
    """清空 projects 表"""

    # 先查看当前数据量
    count_sql = "SELECT COUNT(*) as count FROM projects"
    result = db.fetch_one(count_sql)
    current_count = result["count"] if result else 0

    if current_count == 0:
        print("✅ projects 表已经是空的")
        return

    # 确认删除
    if not force:
        print(f"⚠️  projects 表当前有 {current_count} 条记录")
        try:
            confirm = input("确认清空？(y/N): ").strip().lower()
            if confirm != "y":
                print("❌ 已取消")
                return
        except EOFError:
            print("❌ 请使用 --force 参数或在交互终端运行")
            sys.exit(1)

    # 执行清空
    try:
        # TRUNCATE 更快且重置自增ID
        db.execute("TRUNCATE TABLE projects")
        print(f"✅ 已清空 projects 表 (删除 {current_count} 条记录)")
    except Exception as e:
        # 如果 TRUNCATE 失败（可能有外键约束），用 DELETE
        try:
            db.execute("DELETE FROM projects")
            print(f"✅ 已清空 projects 表 (删除 {current_count} 条记录)")
        except Exception as e2:
            print(f"❌ 清空失败: {e2}")
            sys.exit(1)


def main():
    force = "--force" in sys.argv or "-f" in sys.argv

    # 加载环境变量
    from dotenv import load_dotenv

    load_dotenv()

    print("🗄️  FeishuArchiver 数据库清理工具")
    print("-" * 40)

    clean_projects(force)


if __name__ == "__main__":
    main()
