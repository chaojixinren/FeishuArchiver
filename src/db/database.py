"""
数据库连接模块

[INPUT]: 环境变量配置
[OUTPUT]: 数据库连接和操作方法
[POS]: 管理 MySQL 连接，提供 CRUD 操作
"""

import os
from typing import Optional
from contextlib import contextmanager
import pymysql
from pymysql.cursors import DictCursor


class Database:
    """数据库连接管理"""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ):
        self.host = host or os.getenv("MYSQL_HOST", "localhost")
        self.port = int(port or os.getenv("MYSQL_PORT", "3306"))
        self.user = user or os.getenv("MYSQL_USER", "root")
        self.password = password or os.getenv("MYSQL_PASSWORD", "")
        self.database = database or os.getenv("MYSQL_DATABASE", "feishu")

    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            charset="utf8mb4",
            cursorclass=DictCursor,
        )
        try:
            yield conn
        finally:
            conn.close()

    def execute(self, sql: str, params: Optional[tuple] = None) -> int:
        """执行单条 SQL"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                conn.commit()
                return cursor.rowcount

    def fetch_one(self, sql: str, params: Optional[tuple] = None) -> Optional[dict]:
        """查询单条记录"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                return cursor.fetchone()

    def fetch_all(self, sql: str, params: Optional[tuple] = None) -> list[dict]:
        """查询多条记录"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                return cursor.fetchall()


class ProjectRepository:
    """项目数据仓库"""

    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS projects (
        id INT AUTO_INCREMENT PRIMARY KEY,
        document_id VARCHAR(100) COMMENT '飞书文档ID',
        project_name VARCHAR(255) NOT NULL COMMENT '项目名称',
        project_intro TEXT COMMENT '项目简介',
        project_category VARCHAR(100) COMMENT '项目类别',
        founder_name VARCHAR(100) COMMENT '创始人姓名',
        founder_contact VARCHAR(255) COMMENT '创始人联系方式',
        dx_contact VARCHAR(100) COMMENT 'DX对接人',
        source_channel VARCHAR(100) COMMENT '来源渠道',
        status VARCHAR(50) DEFAULT 'pending' COMMENT '状态',
        score INT DEFAULT NULL COMMENT '项目评分',
        next_action VARCHAR(255) COMMENT '下一步动作',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        INDEX idx_document_id (document_id),
        INDEX idx_status (status)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目信息表'
    """

    INSERT_SQL = """
    INSERT INTO projects (
        document_id, project_name, project_intro, project_category,
        founder_name, founder_contact, dx_contact, source_channel
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    UPDATE_SCORE_SQL = """
    UPDATE projects SET score = %s, next_action = %s, status = 'reviewed'
    WHERE id = %s
    """

    FIND_BY_DOCUMENT_SQL = "SELECT * FROM projects WHERE document_id = %s"

    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()

    def create_table(self) -> None:
        """创建项目表"""
        self.db.execute(self.CREATE_TABLE_SQL)

    def insert(self, project: dict) -> int:
        """插入项目记录"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    self.INSERT_SQL,
                    (
                        project.get("document_id"),
                        project.get("project_name"),
                        project.get("project_intro"),
                        project.get("project_category"),
                        project.get("founder_name"),
                        project.get("founder_contact"),
                        project.get("dx_contact"),
                        project.get("source_channel"),
                    ),
                )
                conn.commit()
                return cursor.lastrowid

    def find_by_document(self, document_id: str) -> list[dict]:
        """根据文档ID查询项目"""
        return self.db.fetch_all(self.FIND_BY_DOCUMENT_SQL, (document_id,))

    def update_score(self, project_id: int, score: int, next_action: str) -> int:
        """更新项目评分"""
        return self.db.execute(self.UPDATE_SCORE_SQL, (score, next_action, project_id))


db = Database()
project_repo = ProjectRepository(db)
