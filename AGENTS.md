# Delta X 项目归档工作流

**Stack:** Python 3.10+ | LangGraph | LangChain | 飞书 API | MySQL

## 结构

```
笔试/
├── main.py                    # CLI 入口
├── src/
│   ├── db/
│   │   └── database.py        # MySQL 连接和操作
│   └── graph/
│       ├── state.py           # WorkflowState TypedDict
│       ├── workflow.py        # LangGraph 状态图定义
│       └── nodes/             # 工作流节点
│           ├── parse_document.py    # 节点1: 文档解析
│           └── extract_and_archive.py  # 节点2: 项目提取归档
└── tests/                     # pytest 测试
```

## 任务导航

| 需求 | 位置 |
|------|------|
| 添加新节点 | `src/graph/nodes/` → 在 `workflow.py` 注册 |
| 修改状态字段 | `src/graph/state.py` → 更新 `WorkflowState` |
| 解析飞书文档 | `src/graph/nodes/parse_document.py` → `FeishuDocParser` |
| 项目数据库操作 | `src/db/database.py` → `ProjectRepository` |
| 运行工作流 | `main.py` → `python main.py --url "..."` |

## 约定

### 状态管理
- 使用 `TypedDict` 定义状态，带 `Annotated` reducer
- 节点返回 `dict` 部分更新，不直接修改状态

```python
class WorkflowState(TypedDict):
    errors: Annotated[list[str], append_list]
```

### 节点模式
- 每个节点是一个纯函数 `(state) -> dict`
- 错误通过 `errors` 字段累积
- 成功时省略 `errors` 字段

### 导入风格
- 使用绝对导入：`from src.graph.state import WorkflowState`
- 不使用 `__init__.py`（namespace package）

## 命令

```bash
# 开发
source .venv/bin/activate
pip install -e ".[dev]"

# 测试
pytest tests/ -v

# 代码检查
ruff check src/

# 运行
python main.py --url "https://xxx.feishu.cn/docx/xxx" --verbose
```

## 环境配置

```bash
# .env
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx
OPENAI_API_KEY=xxx
OPENAI_API_BASE=https://xxx.aliyuncs.com/v1
OPENAI_MODEL_NAME=qwen-plus
MYSQL_HOST=localhost
MYSQL_DATABASE=feishu
MYSQL_USER=root
MYSQL_PASSWORD=xxx
```

飞书应用权限：`docx:document:readonly`

## 架构

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
│ Node 3: 打分决策 │ → 评分 + 下一步动作 (待实现)
└─────────────────┘
```

## MySQL 表结构

`projects` 表：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| document_id | VARCHAR(100) | 飞书文档ID |
| project_name | VARCHAR(255) | 项目名称 |
| project_intro | TEXT | 项目简介 |
| project_category | VARCHAR(100) | 项目类别 |
| founder_name | VARCHAR(100) | 创始人姓名 |
| founder_contact | VARCHAR(255) | 创始人联系方式 |
| dx_contact | VARCHAR(100) | DX对接人 |
| source_channel | VARCHAR(100) | 来源渠道 |
| status | VARCHAR(50) | 状态 (pending/reviewed/approved) |
| score | INT | 评分 |
| next_action | VARCHAR(255) | 下一步动作 |

## 注意事项

- 飞书文档必须分享给应用才能访问
- `FeishuDocParser` 直接调用飞书 API，不依赖 `feishu-docx` 库
- 模型名称通过 `OPENAI_MODEL_NAME` 环境变量配置