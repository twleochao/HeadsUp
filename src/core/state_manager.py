from PySide6.QtCore import QObject, Slot, Signal
from PokerNow.models import GameState, PlayerInfo
from src.core.datatypes import Street
from typing import List

class AppStateManager(QObject):
    ui_pot_updated = Signal(str)
    ui_board_updated = Signal(str)
    ui_hero_cards_updated = Signal(str)

    def __init__(self):
        super().__init__()
        self.current_street: Street = Street.PREFLOP
        self.pot_value: float = 0.0
        self.community_cards: List[str] = []
        self.players: List[PlayerInfo] = []
        self.hero: PlayerInfo = None
        
    @Slot(object)
    def update_raw_game_state(self, raw_state: GameState):
        try:
            # 1. Parse Community Cards and determine street
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
            
            # 3. Parse Player Info and Find Hero
            # --- THIS IS THE CRITICAL SECTION ---
            # Ensure self.players is assigned the list from raw_state
            self.players = raw_state.players 
            self.hero = None
            
            # This loop will now work
            for player in self.players:
                if player.cards and 'Unknown' not in player.cards[0]:
                    self.hero = player
                    
            # 4. Emit signals with new, clean data for UI
            self.ui_pot_updated.emit(str(self.pot_value))
            
            board_str = ", ".join(self.community_cards) if self.community_cards else "---"
            self.ui_board_updated.emit(board_str)
            
            if self.hero:
                hero_cards_str = ", ".join(self.hero.cards)
                self.ui_hero_cards_updated.emit(hero_cards_str)
            else:
                self.ui_hero_cards_updated.emit("Spectator")
        
        except Exception as e:
            print(f"CRITICAL ERROR in AppStateManager: {e}")
            print(f"Problematic raw_state: {raw_state}")


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