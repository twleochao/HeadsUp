import numpy as np
from typing import List, Dict
from src.core.datatypes import Position

RANK_TO_INT = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
SUIT_TO_INT = {'c': 1, 'd': 2, 'h': 3, 's': 4} 

def _format_hand(raw_cards: list[str]) -> str:
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

def _parse_card(card_str: str) -> tuple[int, int]:
    try:
        rank_str, suit_str = card_str.split(' of ')
        rank_map = {
            "Ace": 14, "King": 13, "Queen": 12, "Jack": 11, "10": 10,
            "9": 9, "8": 8, "7": 7, "6": 6, "5": 5, "4": 4, "3": 3, "2": 2
        }
        suit_map = {"Clubs": 1, "Diamonds": 2, "Hearts": 3, "Spades": 4}
        return rank_map.get(rank_str), suit_map.get(suit_str)
    except Exception:
        return 0, 0

def create_feature_vector(hero_cards: List[str], board_cards: List[str], hero_pos: Position, pot_value: float, bet_to_call: float, big_blind: float) -> np.ndarray:
    norm_pot = np.log1p(pot_value / big_blind)
    norm_bet = np.log1p(bet_to_call / big_blind)
    
    h1_rank, h1_suit = _parse_card(hero_cards[0])
    h2_rank, h2_suit = _parse_card(hero_cards[1])
    hand_is_pair = 1.0 if h1_rank == h2_rank else 0.0
    hand_is_suited = 1.0 if h1_suit == h2_suit else 0.0

    b_ranks = [0] * 5
    b_suits = [0] * 5
    for i, card_str in enumerate(board_cards):
        b_ranks[i], b_suits[i] = _parse_card(card_str)
    
    board_flush_possible = 0.0
    suit_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    for s in b_suits:
        if s > 0:
            suit_counts[s] += 1
            if suit_counts[s] >= 3:
                board_flush_possible = 1.0
                
    # TODO: Add more features: straight possible, board pair, etc.
    
    pos_vector = [0.0] * 6
    if hero_pos == Position.BTN: pos_vector[0] = 1.0
    elif hero_pos == Position.SB: pos_vector[1] = 1.0
    elif hero_pos == Position.BB: pos_vector[2] = 1.0
    elif hero_pos in [Position.UTG, Position.UTG1, Position.UTG2]: pos_vector[3] = 1.0
    elif hero_pos == Position.LJ: pos_vector[4] = 1.0
    elif hero_pos == Position.HJ: pos_vector[4] = 1.0
    elif hero_pos == Position.CO: pos_vector[5] = 1.0

    feature_vector = [
        norm_pot, norm_bet,
        h1_rank, h1_suit,
        h2_rank, h2_suit,
        hand_is_pair, hand_is_suited,
    ] + b_ranks + b_suits + [
        board_flush_possible
    ] + pos_vector

    return np.array(feature_vector, dtype=np.float32)