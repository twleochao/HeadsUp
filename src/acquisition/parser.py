import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class Player:
    seat: int
    name: str
    stack: int
    position: Optional[str] = None

@dataclass
class Action:
    street: str
    player: str
    action: str
    amount: Optional[int] = None

@dataclass
class Hand:
    hand_id: str
    date: str
    table: str
    button_seat: int
    stakes: str
    players: List[Player] = field(default_factory=list)
    posts: List[Action] = field(default_factory=list)
    hole_cards: Dict[str, List[str]] = field(default_factory=dict)
    actions: List[Action] = field(default_factory=list)
    board: Dict[str, List[str]] = field(default_factory=lambda: {'FLOP': [], 'TURN': [], 'RIVER': []})
    showdown: Dict[str, List[str]] = field(default_factory=dict)
    winners: List[str] = field(default_factory=list)