"""
Skill Manager - CLI tool for managing Anthropic skills
"""

__version__ = "0.1.0"
__author__ = "Skill Manager Contributors"

from .api_client import AnthropicSkillsClient
from .registry import SkillRegistry
from .validator import SkillValidator

__all__ = ["AnthropicSkillsClient", "SkillRegistry", "SkillValidator"]
