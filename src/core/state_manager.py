from PySide6.QtCore import QObject, Slot, Signal
from PokerNow.models import GameState, PlayerInfo, PlayerState
from src.core.datatypes import Street, Position
from src.api.models import PlayerData
from src.logic.preflop_solver import PreflopSolver
from typing import List

class AppStateManager(QObject):
    ui_pot_updated = Signal(str)
    ui_board_updated = Signal(str)
    ui_hero_cards_updated = Signal(str)
    ui_hero_position_updated = Signal(str)
    ui_turn_updated = Signal(str)
    ui_action_updated = Signal(str)

    def __init__(self):
        super().__init__()
        self.preflop_solver = PreflopSolver()
        self.reset_state()

    def reset_state(self):
        self.current_street: Street = Street.PREFLOP
        self.pot_value: float = 0.0
        self.community_cards: List[str] = []
        self.hero: PlayerData = None
        self.processed_players: List[PlayerData] = []
        self.current_player_name: str = "N/A"
        self.hero_position: Position = Position.UNKNOWN
        
    @Slot(object)
    def update_raw_game_state(self, raw_state: GameState):
        try:
            new_pot = self._parse_stack_value(raw_state.pot_size)
            if new_pot == 0 and self.pot_value > 0:
                self.reset_state()
                self.ui_pot_updated.emit("0")
                self.ui_board_updated.emit("---")
                self.ui_action_updated.emit("---")
                self.ui_hero_cards_updated.emit("---")
                self.ui_hero_position_updated.emit("---")
            self.pot_value = new_pot

            if raw_state.winners:
                self.current_street = Street.SHOWDOWN
                board_str = ", ".join([str(card) for card in raw_state.community_cards])
                self.ui_board_updated.emit(board_str)
                self.ui_pot_updated.emit(str(self.pot_value))
                self.ui_action_updated.emit("---")
                return

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
            self.hero = None
            self.processed_players = []            
            self.current_player_name = raw_state.current_player

            num_players = len(raw_state.players)
            positions = self._calculate_positions(raw_state.dealer_position, num_players)

            raw_hero_card_list = []
            if not self.hero:
                self.processed_players = []
                self.current_player_name = raw_state.current_player
                num_players = len(raw_state.players)
                positions = self._calculate_positions(raw_state.dealer_position, num_players)


                for i, player in enumerate(raw_state.players):
                    is_hero = False
                    if player.cards and 'Unknown' not in player.cards[0]:
                        is_hero = True
                        raw_hero_card_list = player.cards
                        
                    processed_player = PlayerData(
                        name=player.name, 
                        stack=self._parse_stack_value(player.stack),
                        bet=self._parse_stack_value(player.bet_value),
                        is_hero=is_hero,
                        position=positions[i]
                    )
                    self.processed_players.append(processed_player)
                    if is_hero:
                        self.hero = processed_player
                        self.hero_position = processed_player.position
            else:
                raw_hero = next((p for p in raw_state.players if p.name == self.hero_name), None)
                if raw_hero:
                    raw_hero_card_list = raw_hero.cards
            self.current_player_name = raw_state.current_player

            action_to_show = "---"
            if self.hero and self.hero.name == self.current_player_name:
                if self.current_street == Street.PREFLOP:
                    action_to_show = self.preflop_solver.get_preflop_action(
                        self.hero_position,
                        raw_hero_card_list)
                else:
                    action_to_show = "POSTFLOP (TBD)"
            self.ui_action_updated.emit(action_to_show)

            self.ui_pot_updated.emit(str(self.pot_value))
            board_str = ", ".join(self.community_cards) if self.community_cards else "---"
            self.ui_board_updated.emit(board_str)
            
            if self.hero:
                raw_hero = next((p for p in raw_state.players if p.name == self.hero.name), None)
                if raw_hero:
                    hero_cards_str = ", ".join(raw_hero.cards)
                    self.ui_hero_cards_updated.emit(hero_cards_str)
                else:
                    self.ui_hero_cards_updated.emit("Error")
                self.ui_hero_position_updated.emit(self.hero_position.name)
            else:
                self.ui_hero_cards_updated.emit("Spectator")
                self.ui_hero_position_updated.emit("N/A")

            self.ui_turn_updated.emit(self.current_player_name)
        
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

    def _calculate_positions(self, dealer_pos_str: str, num_players: int) -> List[Position]:
        positions = [Position.UNKNOWN] * num_players
        try:
            dealer_idx = int(dealer_pos_str)
        except (ValueError, TypeError):
            return positions

        if num_players < 2:
            return positions

        if num_players == 2:
            positions[dealer_idx] = Position.SB
            positions[(dealer_idx + 1) % num_players] = Position.BB
        elif num_players == 3:
            positions[dealer_idx] = Position.BTN
            positions[(dealer_idx + 1) % num_players] = Position.SB
            positions[(dealer_idx + 2) % num_players] = Position.BB
        elif num_players == 4:
            positions[dealer_idx] = Position.BTN
            positions[(dealer_idx + 1) % num_players] = Position.SB
            positions[(dealer_idx + 2) % num_players] = Position.BB
            positions[(dealer_idx + 3) % num_players] = Position.CO
        elif num_players == 5:
            positions[dealer_idx] = Position.BTN
            positions[(dealer_idx + 1) % num_players] = Position.SB
            positions[(dealer_idx + 2) % num_players] = Position.BB
            positions[(dealer_idx + 3) % num_players] = Position.MP
            positions[(dealer_idx + 4) % num_players] = Position.CO
        elif num_players == 6:
            positions[dealer_idx] = Position.BTN
            positions[(dealer_idx + 1) % num_players] = Position.SB
            positions[(dealer_idx + 2) % num_players] = Position.BB
            positions[(dealer_idx + 3) % num_players] = Position.UTG
            positions[(dealer_idx + 4) % num_players] = Position.MP
            positions[(dealer_idx + 5) % num_players] = Position.CO
        else:
            positions[dealer_idx] = Position.BTN
            positions[(dealer_idx + 1) % num_players] = Position.SB
            positions[(dealer_idx + 2) % num_players] = Position.BB
            
            pos_names = [Position.UTG, Position.MP, Position.CO]
            if num_players == 8:
                pos_names = [Position.UTG, Position.UTG, Position.MP, Position.CO]
            elif num_players == 9:
                pos_names = [Position.UTG, Position.UTG, Position.MP, Position.MP, Position.CO]
            elif num_players == 10:
                pos_names = [Position.UTG, Position.UTG, Position.UTG, Position.MP, Position.MP, Position.CO]

            for i in range(3, num_players - 1):
                positions[(dealer_idx + i) % num_players] = pos_names[i-3]
        
        return positions