from pydantic import BaseModel

class TranscriptSegment(BaseModel):
    text: str
    start: float
    end: float
    sentiment: str | None = None
    emphasis: list[str] = []
