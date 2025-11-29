import eval7
from typing import List

HAND_STRENGTH_TIERS = {
    "VALUE_BET": 25,
    "BLUFF_CATCH": 120,
    "WEAK_PAIR": 400,
    "HIGH_CARD": 1277
}

ACTION_MAP = {
    "FOLD": 0,
    "CHECK_CALL": 1,
    "BET_RAISE": 2
}

class GTOOracle:
    def __init__(self):
        pass

    def get_gto_action(self, hero_cards_str: List[str], board_cards_str: List[str], bet_to_call: float) -> int:
        try:
            hero_hand = [eval7.Card(c) for c in hero_cards_str]
            board = [eval7.Card(c) for c in board_cards_str]
            
            hand_strength_rank = eval7.evaluate(hero_hand + board)

            has_flush_draw = False
            has_straight_draw = False
            
            h1_suit = hero_hand[0].suit
            h2_suit = hero_hand[1].suit
            board_suits = [c.suit for c in board]
            if (board_suits.count(h1_suit) + 1 >= 4) or (board_suits.count(h2_suit) + 1 >= 4):
                has_flush_draw = True
            

            is_facing_bet = bet_to_call > 0

            if hand_strength_rank <= HAND_STRENGTH_TIERS["VALUE_BET"]:
                return ACTION_MAP["BET_RAISE"]

            if has_flush_draw:
                return ACTION_MAP["CHECK_CALL"]

            if hand_strength_rank <= HAND_STRENGTH_TIERS["WEAK_PAIR"]:
                return ACTION_MAP["CHECK_CALL"]

            if is_facing_bet:
                return ACTION_MAP["FOLD"]
            else:
                return ACTION_MAP["CHECK_CALL"]
                
        except Exception as e:
            return ACTION_MAP["CHECK_CALL"]