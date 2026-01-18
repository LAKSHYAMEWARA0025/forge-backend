"""
LLM input/output schemas for Gemini API
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class LLMCaption(BaseModel):
    """Grouped caption from LLM"""
    text: str
    start: float  # seconds
    end: float  # seconds
    word_count: int
    duration_ms: int


class LLMHighlightedWord(BaseModel):
    """Highlighted word specification"""
    captionId: str
    wordStartIndex: int
    wordEndIndex: int


class LLMHighlightStyle(BaseModel):
    """Style for highlighted words"""
    color: str = "#ffd166"
    scale: float = 1.03
    fontWeight: int = 800


class LLMResponse(BaseModel):
    """Expected response from Gemini LLM"""
    title: str = Field(..., description="Short title for the video")
    captions: List[LLMCaption] = Field(..., description="Grouped captions with timestamps")
    highlightedWords: List[LLMHighlightedWord] = Field(..., description="Words to highlight")
    highlightStyle: LLMHighlightStyle = Field(..., description="Style for highlighted words")
