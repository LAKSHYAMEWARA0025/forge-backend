from pydantic import BaseModel

class RefinedTranscript(BaseModel):
    segments: list[dict]
