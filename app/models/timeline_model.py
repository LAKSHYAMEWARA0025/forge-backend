from pydantic import BaseModel

class TimelineEntry(BaseModel):
    text: str
    start: float
    end: float
    style: dict
