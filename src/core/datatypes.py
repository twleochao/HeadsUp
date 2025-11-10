from enum import Enum, auto

class Street(Enum):
    PREFLOP = auto()
    FLOP = auto()
    TURN = auto()
    RIVER = auto()
    SHOWDOWN = auto()

class Position(Enum):
    UNKNOWN = auto()
    SB = auto()
    BB = auto()
    UTG = auto()
    UTG1 = auto()
    UTG2 = auto()
    LJ = auto()
    HJ = auto()
    CO = auto()
    BTN = auto()
    
class Action(Enum):
    FOLD = auto()
    CHECK = auto()
    CALL = auto()
    BET = auto()
    RAISE = auto()