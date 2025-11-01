from pydantic import BaseModel
from typing import Optional
from src.core.datatypes import Position

class PlayerData(BaseModel):
    name: str
    stack: float
    bet: float
    is_hero: bool = False
    position: Optional[Position] = Position.UNKNOWN