"""
提示词模块

统一管理所有 LLM 提示词
"""

from src.prompts.extraction import EXTRACTION_PROMPT
from src.prompts.scoring import SCORING_PROMPT

__all__ = ["EXTRACTION_PROMPT", "SCORING_PROMPT"]