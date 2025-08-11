from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class Player:
    seat: int
    name: str
    stack: float
    pos_id: Optional[int] = None

@dataclass
class Action:
    street: str
    player: str
    action: str
    amount: float | None = None

@dataclass
class Hand:
    hand_id: str
    table_name: str
    stakes: str
    button_seat: int
    players: List[Player] = field(default_factory=list)
    actions: List[Action] = field(default_factory=list)
    board: Dict[str, List[str]] = field(default_factory=lambda: {"FLOP": [], "TURN": [], "RIVER": []})
    showdown: Dict[str, List[str]] = field(default_factory=dict)
    winners: List[str] = field(default_factory=list)
    win_amounts: Dict[str, float] = field(default_factory=dict)
