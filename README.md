# FeishuArchiver

从飞书智能纪要自动提取项目信息、智能评分并归档到 MySQL。

## 快速开始

```bash
# 安装
pip install -e ".[dev]"

# 配置
cp .env.example .env
# 编辑 .env 填入飞书应用凭证、LLM 配置和 MySQL 配置

# 运行
python main.py --url "https://xxx.feishu.cn/docx/xxx"
```

## 工作流

```
[飞书文档] → 解析 → LLM提取 → 智能评分 → MySQL存储
```

### 节点说明

| 节点 | 功能 |
|------|------|
| parse_document | 解析飞书文档，获取 Markdown 内容 |
| extract_and_archive | LLM 提取项目信息，存入数据库 |
| score_and_decide | LLM 智能评分，生成下一步动作建议 |

### 评分规则

- **8-10 分**: 高潜力项目，状态设为 `approved`
- **5-7 分**: 正常项目，状态设为 `reviewed`
- **1-4 分**: 待观察项目，状态设为 `rejected`

## 环境变量

| 变量 | 说明 |
|------|------|
| FEISHU_APP_ID | 飞书应用 ID |
| FEISHU_APP_SECRET | 飞书应用密钥 |
| OPENAI_API_KEY | LLM API Key |
| OPENAI_API_BASE | LLM API Base URL（可选） |
| OPENAI_MODEL_NAME | 模型名称，默认 qwen-plus |
| MYSQL_HOST | MySQL 主机 |
| MYSQL_PORT | MySQL 端口 |
| MYSQL_DATABASE | 数据库名 |
| MYSQL_USER | 数据库用户 |
| MYSQL_PASSWORD | 数据库密码 |

## 项目结构

```
src/
├── db/database.py           # MySQL 操作、ProjectStatus 常量
├── llm/__init__.py          # LLM 客户端、JSON 解析工具
├── prompts/                 # LLM 提示词
│   ├── extraction.py        # 项目提取提示词
│   └── scoring.py           # 项目评分提示词
└── graph/
    ├── state.py             # 工作流状态定义
    ├── workflow.py          # LangGraph 工作流
    └── nodes/
        ├── parse_document.py      # 节点1: 解析文档
        ├── extract_and_archive.py # 节点2: 提取归档
        └── score_and_decide.py    # 节点3: 评分决策

scripts/
└── clean_db.py              # 数据库清理工具

tests/                       # pytest 测试
```

## 脚本工具

### 清理数据库

```bash
# 交互式清理
python scripts/clean_db.py

# 强制清理（跳过确认）
python scripts/clean_db.py --force
```

## 测试

```bash
pytest tests/ -v
```

## Tech Stack

Python 3.10+ | LangGraph | LangChain | 飞书 API | MySQL