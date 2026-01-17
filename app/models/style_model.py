from pydantic import BaseModel

class StyleConfig(BaseModel):
    font_size: int = 24
    highlight_color: str = "#FFD600"
    animation: str = "fade"
