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
        """
        A simple rule-based GTO-Lite oracle.
        Returns 0 (Fold), 1 (Check/Call), or 2 (Bet/Raise).
        """
        try:
            # 1. Evaluate current hand strength
            hero_hand = [eval7.Card(c) for c in hero_cards_str]
            board = [eval7.Card(c) for c in board_cards_str]
            
            # eval7.evaluate returns a rank from 1 (best) to 1277 (worst)
            hand_strength_rank = eval7.evaluate(hero_hand + board)

            # 2. Check for Draws
            has_flush_draw = False
            has_straight_draw = False
            
            # (Simple draw logic for MVP)
            h1_suit = hero_hand[0].suit
            h2_suit = hero_hand[1].suit
            board_suits = [c.suit for c in board]
            if (board_suits.count(h1_suit) + 1 >= 4) or (board_suits.count(h2_suit) + 1 >= 4):
                has_flush_draw = True
            
            # (Straight draw logic is complex; we'll skip for the MVP)

            # 3. Decision-Making Logic
            is_facing_bet = bet_to_call > 0

            # --- VALUE ---
            if hand_strength_rank <= HAND_STRENGTH_TIERS["VALUE_BET"]:
                return ACTION_MAP["BET_RAISE"] # Always bet/raise our monsters

            # --- DRAWS ---
            if has_flush_draw:
                return ACTION_MAP["CHECK_CALL"] # Always call/check with a good draw

            # --- BLUFF CATCHER / WEAK PAIR ---
            if hand_strength_rank <= HAND_STRENGTH_TIERS["WEAK_PAIR"]:
                return ACTION_MAP["CHECK_CALL"] # Check/call with any pair

            # --- AIR / HIGH CARD ---
            if is_facing_bet:
                return ACTION_MAP["FOLD"] # Fold if we have air and face a bet
            else:
                return ACTION_MAP["CHECK_CALL"] # Check if we have air and no bet
                
        except Exception as e:
            # print(f"Oracle Error: {e} with {hero_cards_str}, {board_cards_str}")
            return ACTION_MAP["CHECK_CALL"] # Default to passive