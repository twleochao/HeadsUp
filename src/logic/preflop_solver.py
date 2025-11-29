import os
import json
from src.core.datatypes import Position

CARD_ORDER = "AKQJT98765432"
PAIR_ORDER = [c*2 for c in CARD_ORDER]
SUITED_ORDER = {rank: i for i, rank in enumerate(CARD_ORDER)}

def _parse_range_notation(notation_list: list) -> set:
    hands = set()
    for notation in notation_list:
        if not notation:
            continue
            
        if len(notation) == 5 and notation[0] == notation[1] and notation[3] == notation[4]:
            try:
                start_idx = PAIR_ORDER.index(notation[:2])
                end_idx = PAIR_ORDER.index(notation[3:])
                for i in range(start_idx, end_idx + 1):
                    hands.add(PAIR_ORDER[i])
            except ValueError:
                pass
        
        elif len(notation) == 7 and notation[2] == 's' and notation[6] == 's':
            try:
                high_card = notation[0]
                start_rank = notation[1]
                end_rank = notation[4]
                start_idx = SUITED_ORDER[start_rank]
                end_idx = SUITED_ORDER[end_rank]
                for i in range(start_idx, end_idx + 1):
                    hands.add(f"{high_card}{CARD_ORDER[i]}s")
            except (KeyError, IndexError):
                pass
                
        # 3. Handle Offsuit (e.g., "AKo-ATo")
        elif len(notation) == 7 and notation[2] == 'o' and notation[6] == 'o':
            try:
                high_card = notation[0]
                start_rank = notation[1]
                end_rank = notation[4]
                start_idx = SUITED_ORDER[start_rank]
                end_idx = SUITED_ORDER[end_rank]
                for i in range(start_idx, end_idx + 1):
                    hands.add(f"{high_card}{CARD_ORDER[i]}o")
            except (KeyError, IndexError):
                pass

        elif len(notation) in [2, 3]:
            hands.add(notation)
            
    return hands
class PreflopSolver:
    def __init__(self, chart_path: str = "data/charts/rfi_9max.json"):
        self.charts = {}
        try:
            with open(chart_path, 'r') as f:
                raw_charts = json.load(f)
            
            for pos, actions in raw_charts.items():
                self.charts[pos] = {}
                for action, notation_list in actions.items():
                    parsed_hands = _parse_range_notation(notation_list)
                    for hand in parsed_hands:
                        self.charts[pos][hand] = action

            print(f"Successfully loaded and parsed preflop chart: {chart_path}")

        except Exception as e:
            print(f"error: {e}")

    def _format_hand(self, raw_cards: list[str]) -> str:
        if not raw_cards or len(raw_cards) != 2:
            return ""

        card1_rank, card1_suit = raw_cards[0].split(' of ')
        card2_rank, card2_suit = raw_cards[1].split(' of ')

        rank_map = {
            "Ace": "A", "King": "K", "Queen": "Q", "Jack": "J",
            "10": "T", "9": "9", "8": "8", "7": "7", "6": "6",
            "5": "5", "4": "4", "3": "3", "2": "2"
        }
        
        r1 = rank_map.get(card1_rank, "?")
        r2 = rank_map.get(card2_rank, "?")

        ranks = "AKQJT98765432"
        if ranks.index(r1) > ranks.index(r2):
            r1, r2 = r2, r1

        if r1 == r2:
            return f"{r1}{r2}"
        elif card1_suit == card2_suit:
            return f"{r1}{r2}s"
        else:
            return f"{r1}{r2}o"
    def get_preflop_action(self, position: Position, raw_hero_cards: list[str], current_bet: float, big_blind: float) -> dict:
        default_action = {"action": "FOLD", "amount_str": ""}
        
        if current_bet > big_blind:
            return {"action": "vs Open", "amount_str": "No Chart"}
            
        if not raw_hero_cards or position == Position.UNKNOWN:
            return default_action
            
        hand = self._format_hand(raw_hero_cards)
        pos_name = position.name

        position_key_map = {
            "UTG": "UTG",
            "UTG1": "UTG+1",
            "UTG2": "UTG+2",
            "LJ": "Lojack",
            "HJ": "Hijack",
            "CO": "Cutoff",
            "BTN": "Button",
            "SB": "Small Blind",
            "BB": "Big Blind"
        }
        
        chart_key = position_key_map.get(pos_name)
        if not chart_key or chart_key not in self.charts:
            return {"action": "---", "amount_str": f"No chart for {pos_name}"}
        
        action = self.charts[chart_key].get(hand, "FOLD")
        
        if action == "Raise":
            return {"action": "RAISE", "amount_str": "3bb"}
        elif action == "Limp":
            return {"action": "LIMP", "amount_str": ""}
        else:
            return {"action": "FOLD", "amount_str": ""}