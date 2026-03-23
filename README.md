# ProjectScribe / 智归档

从飞书智能纪要自动提取项目信息并归档到 MySQL。

## 快速开始

```bash
# 安装
pip install -e ".[dev]"

# 配置
cp .env.example .env
# 编辑 .env 填入飞书应用凭证和 MySQL 配置

# 运行
python main.py --url "https://xxx.feishu.cn/docx/xxx"
```

## 工作流

```
[飞书文档] → 解析 → LLM提取 → MySQL存储
```

## 环境变量

| 变量 | 说明 |
|------|------|
| FEISHU_APP_ID | 飞书应用 ID |
| FEISHU_APP_SECRET | 飞书应用密钥 |
| OPENAI_API_KEY | LLM API Key |
| OPENAI_MODEL_NAME | 模型名称 |
| MYSQL_HOST | MySQL 主机 |
| MYSQL_DATABASE | 数据库名 |
| MYSQL_USER | 数据库用户 |
| MYSQL_PASSWORD | 数据库密码 |

## 项目结构

```
src/
├── db/database.py           # MySQL 操作
└── graph/
    ├── state.py             # 工作流状态
    ├── workflow.py          # LangGraph 定义
    └── nodes/
        ├── parse_document.py      # 节点1: 解析文档
        └── extract_and_archive.py # 节点2: 提取归档

tests/                       # pytest 测试
```

## 测试

```bash
pytest tests/ -v
```

## Tech Stack

Python 3.10+ | LangGraph | LangChain | 飞书 API | MySQL