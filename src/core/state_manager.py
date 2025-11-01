from PySide6.QtCore import QObject, Slot
from PokerNow.models import GameState, PlayerInfo
from src.core.datatypes import Street
from typing import List

class AppStateManager(QObject):
    def __init__(self):
        super().__init__()
        self.current_street: Street = Street.PREFLOP
        self.pot_value: float = 0.0
        self.community_cards: List[str] = []
        
    @Slot(object)
    def update_raw_game_state(self, raw_state: GameState):
        self.community_cards = [str(card) for card in raw_state.community_cards]
        
        num_cards = len(self.community_cards)
        if num_cards == 0:
            self.current_street = Street.PREFLOP
        elif num_cards == 3:
            self.current_street = Street.FLOP
        elif num_cards == 4:
            self.current_street = Street.TURN
        elif num_cards == 5:
            self.current_street = Street.RIVER
        
        # 2. Parse Pot
        self.pot_value = self._parse_stack_value(raw_state.pot_size)
        
        # 3. TODO: Parse Player Info (stacks, bets, positions)
        
        # 4. TODO: Identify Hero
        
        # 5. TODO: Normalize data (feature engineering)
        
        # 6. TODO: Emit signals with new, clean data for UI and Solvers
        
        # For testing, print the current street
        print(f"Parsed State: Street: {self.current_street.name}, Pot: {self.pot_value}, Board: {self.community_cards}")


    def _parse_stack_value(self, stack_str: str) -> float:
        if not stack_str:
            return 0.0
        
        stack_str = stack_str.strip().upper()
        
        if 'K' in stack_str:
            return float(stack_str.replace('K', '')) * 1000
        if 'M' in stack_str:
            return float(stack_str.replace('M', '')) * 1000000
        
        try:
            return float(stack_str)
        except ValueError:
            return 0.0