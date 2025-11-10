from PySide6.QtCore import QObject, Slot, Signal
from PokerNow.models import GameState, PlayerInfo, PlayerState
from src.core.datatypes import Street, Position
from src.api.models import PlayerData
from src.logic.preflop_solver import PreflopSolver
from src.logic.postflop_solver import PostflopSolver
from src.core.feature_eng import create_feature_vector
from typing import List, Dict
import uuid
import numpy as np 

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
        self.postflop_solver = PostflopSolver()
        self.hand_id: str = "N/A"
        self.big_blind: float = 2.0
        self.reset_state()

    def reset_state(self):
        self.hand_id = str(uuid.uuid4())
        self.current_street: Street = Street.PREFLOP
        self.pot_value: float = 0.0
        self.community_cards: List[str] = []
        self.hero: PlayerData = None
        self.current_player_name: str = "N/A"
        self.hero_position: Position = Position.UNKNOWN
        self.big_blind = 2.0

        self.hand_in_progress: bool = False
        self.hero_cards_str: str = "---"
        self.player_positions: Dict[str, Position] = {}

        self.is_awaiting_hero_action: bool = False
        self.previous_hero_bet: float = 0.0
        self.current_bet_to_call: float = 0.0
        self.previous_pot_value: float = 0.0
        self.gto_action_to_log: dict = {}
        self.hand_id = str(uuid.uuid4())

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

            max_bet = 0.0
            for p in raw_state.players:
                bet_val = self._parse_stack_value(p.bet_value)
                if bet_val > max_bet:
                    max_bet = bet_val
            self.current_bet_to_call = max_bet 

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

            if self.hero and self.hero.name == self.current_player_name:
                if not self.is_awaiting_hero_action:
                    print(f"bet to call : {self.current_bet_to_call}")
                    self.is_awaiting_hero_action = True

                    hero_raw = next((p for p in raw_state.players if p.name == self.hero.name), None)
                    self.previous_hero_bet = self._parse_stack_value(hero_raw.bet_value) if hero_raw else 0.0
                    self.previous_pot_value = self.pot_value

                    if raw_state.blinds and len(raw_state.blinds) > 1:
                        self.big_blind = self._parse_stack_value(raw_state.blinds[1])

                    if self.current_street == Street.PREFLOP:
                        self.gto_action_to_log = self.preflop_solver.get_preflop_action(
                            self.hero_position,
                            self.hero_cards_str.split(', '),
                            self.current_bet_to_call,
                            self.big_blind 
                        )
                    else:
                        features = create_feature_vector(
                            hero_cards=self.hero_cards_str.split(', '),
                            board_cards=self.community_cards,
                            hero_pos=self.hero_position,
                            pot_value=self.pot_value,
                            bet_to_call=self.current_bet_to_call,
                            big_blind=self.big_blind
                        )
                        self.gto_action_to_log = self.postflop_solver.get_postflop_action(features)
                
                action_to_show = f"{self.gto_action_to_log.get('action', '---')} {self.gto_action_to_log.get('amount_str', '')}"
                self.ui_action_updated.emit(action_to_show.strip())

            elif self.hero and self.is_awaiting_hero_action:
                print("Hero has acted. Detecting action...")
                self.is_awaiting_hero_action = False
                
                hero_raw = next((p for p in raw_state.players if p.name == self.hero.name), None)
                hero_action = "UNKNOWN"
                hero_action_amount = 0.0
                
                if hero_raw:
                    new_bet = self._parse_stack_value(hero_raw.bet_value)
                    
                    if hero_raw.status == PlayerState.FOLDED:
                        hero_action = "FOLD"
                    elif new_bet == self.previous_hero_bet:
                        hero_action = "CHECK"
                    elif new_bet == self.current_bet_to_call:
                        hero_action = "CALL"
                        hero_action_amount = new_bet - self.previous_hero_bet
                    elif new_bet > self.current_bet_to_call:
                        hero_action = "BET" if self.current_bet_to_call == 0 else "RAISE"
                        hero_action_amount = new_bet - self.previous_hero_bet
                
                print(f"action: {hero_action} {hero_action_amount}")

                log_data = {
                    "hand_id": self.hand_id,
                    "street": self.current_street.name,
                    "hero_cards": self.hero_cards_str,
                    "hero_pos": self.hero_position.name,
                    "board_cards": ", ".join(self.community_cards) if self.community_cards else "",
                    "pot_value": self.previous_pot_value,
                    "hero_action": hero_action,
                    "hero_action_amount": hero_action_amount,
                    "gto_action": self.gto_action_to_log.get('action'),
                    "gto_action_amount": self.gto_action_to_log.get('amount_str')
                }
                self.log_decision_made.emit(log_data)
                self.ui_action_updated.emit("---")

            elif not self.is_awaiting_hero_action:
                self.ui_action_updated.emit("---")
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

        pos_map = {
            2: [Position.BB, Position.BTN],
            3: [Position.BB, Position.SB, Position.BTN],
            4: [Position.BB, Position.SB, Position.BTN, Position.CO],
            5: [Position.BB, Position.SB, Position.BTN, Position.CO, Position.HJ],
            6: [Position.BB, Position.SB, Position.BTN, Position.CO, Position.HJ, Position.LJ],
            7: [Position.BB, Position.SB, Position.BTN, Position.CO, Position.HJ, Position.LJ, Position.UTG2],
            8: [Position.BB, Position.SB, Position.BTN, Position.CO, Position.HJ, Position.LJ, Position.UTG2, Position.UTG1],
            9: [Position.BB, Position.SB, Position.BTN, Position.CO, Position.HJ, Position.LJ, Position.UTG2, Position.UTG1, Position.UTG],
            10: [Position.BB, Position.SB, Position.BTN, Position.CO, Position.HJ, Position.LJ, Position.UTG2, Position.UTG1, Position.UTG, Position.UTG] 
        }

        current_pos = pos_map.get(num_players, [Position.UNKNOWN] * num_players)
        
        for i in range(num_players):
            pos_index = (i - 2) % num_players
            positions[(dealer_idx + i) % num_players] = current_pos[pos_index]
        return positions