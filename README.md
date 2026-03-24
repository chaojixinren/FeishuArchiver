# FeishuArchiver

从飞书智能纪要自动提取项目信息、智能评分并归档到 MySQL。

## 功能特性

- **自动解析飞书文档**: 通过飞书 API 获取文档内容并转换为 Markdown
- **智能信息提取**: 使用 LLM 从会议纪要中提取项目关键信息
- **项目智能评分**: 基于团队背景、市场潜力、产品成熟度三个维度进行评估
- **决策建议生成**: 自动生成具体可执行的下一步动作建议
- **数据库持久化**: 项目信息自动存储到 MySQL，便于后续管理

## 快速开始

```bash
# 克隆项目
git clone <repository-url>
cd 笔试

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 安装依赖
pip install -e ".[dev]"

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入飞书应用凭证、LLM 配置和 MySQL 配置

# 运行
python main.py --url "https://xxx.feishu.cn/docx/xxx"
python main.py --url "https://xxx.feishu.cn/docx/xxx" --verbose  # 详细输出
```

## 工作流架构

```
[飞书文档 URL]
      │
      ▼
┌─────────────────┐
│ Node 1: 解析文档 │ → Markdown 内容
└─────────────────┘
      │
      ▼
┌─────────────────┐
│ Node 2: 提取归档 │ → 项目信息列表 → MySQL
└─────────────────┘
      │
      ▼
┌─────────────────┐
│ Node 3: 评分决策 │ → 评分 + 下一步动作
└─────────────────┘
```

### 节点说明

| 节点 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `parse_document` | 解析飞书文档 | 文档 URL | Markdown 内容 |
| `extract_and_archive` | LLM 提取项目信息 | 文档内容 | 项目列表 → MySQL |
| `score_and_decide` | LLM 智能评分 | 项目列表 | 评分 + 决策建议 |

### 评分规则

项目评分范围 1-10 分，基于三个维度：

| 维度 | 权重 | 评估内容 |
|------|------|---------|
| 团队背景 | 35% | 创始人经验、团队完整性、过往业绩 |
| 市场潜力 | 35% | 市场规模、增长趋势、竞争格局 |
| 产品成熟度 | 30% | 产品阶段、技术壁垒、商业模式清晰度 |

评分与状态映射：

| 分数范围 | 状态 | 说明 |
|---------|------|------|
| 8-10 分 | `approved` | 高潜力项目 |
| 5-7 分 | `reviewed` | 正常项目 |
| 1-4 分 | `rejected` | 待观察项目 |

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `FEISHU_APP_ID` | ✅ | 飞书应用 ID |
| `FEISHU_APP_SECRET` | ✅ | 飞书应用密钥 |
| `OPENAI_API_KEY` | ✅ | LLM API Key |
| `OPENAI_API_BASE` | ❌ | LLM API Base URL（兼容 OpenAI 接口） |
| `OPENAI_MODEL_NAME` | ❌ | 模型名称，默认 `qwen-plus` |
| `MYSQL_HOST` | ✅ | MySQL 主机 |
| `MYSQL_PORT` | ❌ | MySQL 端口，默认 `3306` |
| `MYSQL_DATABASE` | ✅ | 数据库名 |
| `MYSQL_USER` | ✅ | 数据库用户 |
| `MYSQL_PASSWORD` | ✅ | 数据库密码 |

## 项目结构

```
笔试/
├── main.py                      # CLI 入口
├── pyproject.toml               # 项目配置
├── requirements.txt             # 依赖清单
├── .env.example                 # 环境变量示例
│
├── src/
│   ├── db/
│   │   └── database.py          # MySQL 连接和操作
│   │
│   ├── llm/
│   │   └── __init__.py          # LLM 客户端、JSON 解析工具
│   │
│   ├── prompts/
│   │   ├── extraction.py        # 项目提取提示词
│   │   └── scoring.py           # 项目评分提示词
│   │
│   └── graph/
│       ├── state.py             # WorkflowState TypedDict
│       ├── workflow.py          # LangGraph 状态图定义
│       └── nodes/
│           ├── parse_document.py      # 节点1: 文档解析
│           ├── extract_and_archive.py # 节点2: 项目提取归档
│           └── score_and_decide.py    # 节点3: 评分决策
│
├── scripts/
│   └── clean_db.py              # 数据库清理工具
│
└── tests/                       # pytest 测试
    ├── conftest.py
    ├── test_parse_document.py
    ├── test_extract_and_archive.py
    └── test_score_and_decide.py
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
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_parse_document.py -v
```

## MySQL 表结构

`projects` 表：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INT | 主键，自增 |
| `document_id` | VARCHAR(100) | 飞书文档ID |
| `project_name` | VARCHAR(255) | 项目名称 |
| `project_intro` | TEXT | 项目简介 |
| `project_category` | VARCHAR(100) | 项目类别 |
| `founder_name` | VARCHAR(100) | 创始人姓名 |
| `founder_contact` | VARCHAR(255) | 创始人联系方式 |
| `dx_contact` | VARCHAR(100) | DX对接人 |
| `source_channel` | VARCHAR(100) | 来源渠道 |
| `status` | VARCHAR(50) | 状态 (pending/reviewed/approved/rejected) |
| `score` | INT | 评分 (1-10) |
| `next_action` | VARCHAR(255) | 下一步动作 |
| `created_at` | TIMESTAMP | 创建时间 |
| `updated_at` | TIMESTAMP | 更新时间 |

## 开发指南

### 代码规范

```bash
# 代码检查
ruff check src/

# 自动修复
ruff check src/ --fix
```

### 添加新节点

1. 在 `src/graph/nodes/` 创建新节点文件
2. 实现节点函数 `(state) -> dict`
3. 在 `src/graph/workflow.py` 注册节点和边

### 状态管理约定

- 使用 `TypedDict` 定义状态，带 `Annotated` reducer
- 节点返回 `dict` 部分更新，不直接修改状态
- 错误通过 `errors` 字段累积

```python
class WorkflowState(TypedDict):
    errors: Annotated[list[str], append_list]
```

## 注意事项

- 飞书文档必须分享给应用才能访问
- 飞书应用权限要求：`docx:document:readonly`
- `FeishuDocParser` 直接调用飞书 API，不依赖 `feishu-docx` 库
- LLM 需兼容 OpenAI 接口（支持阿里云、DeepSeek 等）

## Tech Stack

Python 3.10+ | LangGraph | LangChain | 飞书 API | MySQL | PyMySQL

## License

MIT