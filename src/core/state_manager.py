from PySide6.QtCore import QObject, Slot, Signal
from PokerNow.models import GameState, PlayerInfo, PlayerState
from src.core.datatypes import Street, Position
from src.api.models import PlayerData
from src.logic.preflop_solver import PreflopSolver
from typing import List, Dict
import uuid

class AppStateManager(QObject):
    ui_pot_updated = Signal(str)
    ui_board_updated = Signal(str)
    ui_hero_cards_updated = Signal(str)
    ui_hero_position_updated = Signal(str)
    ui_turn_updated = Signal(str)
    ui_action_updated = Signal(str)
    log_decision_made = Signal(dict)

    def __init__(self):
        super().__init__()
        self.preflop_solver = PreflopSolver()
        self.hand_id: str = "N/A"
        self.reset_state()

    def reset_state(self):
        self.hand_id = str(uuid.uuid4())
        self.current_street: Street = Street.PREFLOP
        self.pot_value: float = 0.0
        self.community_cards: List[str] = []
        self.hero: PlayerData = None
        self.current_player_name: str = "N/A"
        self.hero_position: Position = Position.UNKNOWN

        self.hand_in_progress: bool = False
        self.hero_cards_str: str = "---"
        self.player_positions: Dict[str, Position] = {}

        self.ui_pot_updated.emit("0")
        self.ui_board_updated.emit("---")
        self.ui_action_updated.emit("---")
        self.ui_hero_cards_updated.emit("---")
        self.ui_hero_position_updated.emit("---")
        
    @Slot(object)
    def update_raw_game_state(self, raw_state: GameState):
        try:
            if raw_state.winners and self.hand_in_progress:
                self.hand_in_progress = False
                self.current_street = Street.SHOWDOWN
                board_str = ", ".join([str(card) for card in raw_state.community_cards])
                self.ui_board_updated.emit(board_str)
                self.ui_pot_updated.emit(str(self._parse_stack_value(raw_state.pot_size)))
                self.ui_action_updated.emit("---")
                return

            if not self.hand_in_progress and not raw_state.winners and not raw_state.community_cards:
                if not raw_state.players or not raw_state.players[0].cards:
                    return

                self.hand_in_progress = True

                num_players = len(raw_state.players)
                positions = self._calculate_positions(raw_state.dealer_position, num_players)
                self.player_positions = {}

                for i, player in enumerate(raw_state.players):
                    if player.name:
                        self.player_positions[player.name] = positions[i]

                    if player.cards and 'Unknown' not in player.cards[0]:
                        self.hero = PlayerData(
                            name=player.name,
                            stack=self._parse_stack_value(player.stack),
                            bet=self._parse_stack_value(player.bet_value),
                            is_hero=True,
                            position=positions[i]
                        )
                        self.hero_position = positions[i]
                        self.hero_cards_str = ", ".join(player.cards)

                if self.hero:
                    self.ui_hero_cards_updated.emit(self.hero_cards_str)
                    self.ui_hero_position_updated.emit(self.hero_position.name)
                else:
                    self.ui_hero_cards_updated.emit("Spectator")
                    self.ui_hero_position_updated.emit("N/A")
            

            if not self.hand_in_progress: 
                return

            self.pot_value = self._parse_stack_value(raw_state.pot_size)
            self.current_player_name = raw_state.current_player
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
            

            action_to_show = "---"
            if self.hero and self.hero.name == self.current_player_name:
                if self.current_street == Street.PREFLOP:
                    action_to_show = self.preflop_solver.get_preflop_action(self.hero_position, self.hero_cards_str.split(', '))
                else:
                    action_to_show = "POSTFLOP (TBD)"

            log_data = {
                "hand_id": self.hand_id,
                "street": self.current_street.name,
                "hero_cards": self.hero_cards_str,
                "hero_pos": self.hero_position.name,
                "board_cards": ", ".join(self.community_cards) if self.community_cards else "",
                "pot_value": self.pot_value,
                "hero_action": "UNKNOWN", # <-- TODO: Get this from the API
                "gto_action": action_to_show
            }

            self.log_decision_made.emit(log_data)
            self.ui_action_updated.emit(action_to_show)
            self.ui_pot_updated.emit(str(self.pot_value))
            board_str = ", ".join(self.community_cards) if self.community_cards else "---"
            self.ui_board_updated.emit(board_str)
            self.ui_turn_updated.emit(self.current_player_name)

        except Exception as e:
            print(f"ERROR: {e}")
            print(f"raw_state: {raw_state}")

    def _parse_stack_value(self, stack_str: str) -> float:
        if not stack_str or "all in" in stack_str.lower():
            return 0.0
        
        stack_str = stack_str.strip().upper().split('(')[0]
        
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

        if num_players < 2 or dealer_idx >= num_players or dealer_idx < 0:
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