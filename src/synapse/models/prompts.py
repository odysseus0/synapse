"""
Pydantic models for prompt configurations.
"""
from pydantic import BaseModel


class PromptDetail(BaseModel):
    """Model for a single prompt template with system and user messages."""
    system_message: str
    user_message_template: str


class PromptConfig(BaseModel):
    """Top-level model for the prompt configuration."""
    map_prompt: PromptDetail
    reduce_prompt: PromptDetail