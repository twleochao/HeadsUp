from pydantic import BaseModel
from typing import Optional
from src.core.datatypes import Position # We will use Position later

class PlayerData(BaseModel):
    name: str
    stack: float
    bet: float
    is_hero: bool = False
    # position: Optional[Position] = None # We will add this in the next step