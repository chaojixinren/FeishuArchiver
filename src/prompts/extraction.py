"""
项目信息提取提示词

用于从会议纪要中提取项目相关信息
"""

EXTRACTION_PROMPT = """你是一个项目信息提取助手。请从以下会议纪要中提取项目相关信息。

会议纪要内容：
{document_content}

请仔细分析文档，提取所有提到的项目信息。

返回 JSON 格式，包含 projects 数组：
```json
{{
  "projects": [
    {{
      "project_name": "项目名称",
      "project_intro": "项目简介",
      "project_category": "项目类别",
      "founder_name": "创始人姓名",
      "founder_contact": "联系方式",
      "dx_contact": "DX对接人",
      "source_channel": "来源渠道"
    }}
  ]
}}
```

注意：
- 如果文档中提到了多个项目，请分别提取
- 如果某个字段没有明确提到，使用空字符串 ""
- 如果完全没有项目信息，返回 {{"projects": []}}
- 只返回 JSON，不要其他文字
"""