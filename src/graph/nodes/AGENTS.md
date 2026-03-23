# 工作流节点模块

L2 | 父级: ../AGENTS.md

## 职责

每个文件定义一个 LangGraph 节点函数：

```python
def node_name(state: WorkflowState) -> dict:
    # 处理逻辑
    return {"field": "value"}
```

## 节点实现模式

### 输入验证
```python
url = state.get("feishu_url", "")
if not url:
    return {"errors": ["错误: 未提供URL"], "current_node": "node_name"}
```

### 错误处理
```python
try:
    # API 调用
except Exception as e:
    return {"errors": [f"操作失败: {e}"], "current_node": "node_name"}
```

### 成功返回
```python
return {
    "result_field": data,
    "current_node": "node_name"
}
```

## 文件清单

| 文件 | 节点 | 功能 |
|------|------|------|
| `parse_document.py` | `parse_document_node` | 解析飞书文档 → Markdown |

## 添加新节点

1. 创建 `new_node.py`
2. 实现 `new_node_node(state) -> dict`
3. 在 `src/graph/workflow.py` 注册：
   ```python
   from src.graph.nodes.new_node import new_node_node
   builder.add_node("new_node", new_node_node)
   builder.add_edge("parse_document", "new_node")
   ```

## FeishuDocParser

`parse_document.py` 中的核心类：

- `_get_token()` — 获取 tenant_access_token
- `get_document_content(doc_id)` — 获取文档并转 Markdown
- `_blocks_to_markdown(blocks)` — Block → Markdown 转换

支持的 Block 类型：text(2), heading1-6(3-8), bullet(12), ordered(13), code(14), quote(15)