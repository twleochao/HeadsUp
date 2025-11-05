import os
import json
from src.core.datatypes import Position

STUB_RFI_CHARTS = {
    "BTN": {
        "AA": "RAISE 3bb", "KK": "RAISE 3bb", "QQ": "RAISE 3bb", "JJ": "RAISE 3bb",
        "AKs": "RAISE 3bb", "AQs": "RAISE 3bb", "AJs": "RAISE 3bb", "ATs": "RAISE 3bb",
        "KQs": "RAISE 3bb", "KJs": "RAISE 3bb", "KTs": "RAISE 3bb",
        "AKo": "RAISE 3bb", "AQo": "RAISE 3bb",
        "72o": "FOLD", "83o": "FOLD", "T4s": "FOLD"
    },
    "SB": {
        "AA": "RAISE 3bb", "KK": "RAISE 3bb", "QQ": "RAISE 3bb", "JJ": "RAISE 3bb",
        "T9s": "RAISE 3bb", "98s": "RAISE 3bb", "87s": "RAISE 3bb", "76s": "RAISE 3bb",
        "AKs": "RAISE 3bb", "AQs": "RAISE 3bb", "AJs": "RAISE 3bb", "ATs": "RAISE 3bb",
        "AKo": "RAISE 3bb", "AQo": "RAISE 3bb", "AJo": "RAISE 3bb",
        "72o": "FOLD", "83o": "FOLD"
    },
    "BB": {
        "AA": "3-BET 4x", "KK": "3-BET 4x", "QQ": "3-BET 4x",
        "72o": "CHECK/FOLD"
    }
}

class PreflopSolver:
    def __init__(self, chart_path: str = None):
        if chart_path:
            # TODO: Add logic to load charts from 'data/charts/'
            print("Chart loading not yet implemented. Using stubs.")
            self.charts = STUB_RFI_CHARTS
        else:
            print("Using stub preflop charts for development.")
            self.charts = STUB_RFI_CHARTS

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

    def get_preflop_action(self, position: Position, raw_hero_cards: list[str]) -> str:
        if not raw_hero_cards or position == Position.UNKNOWN:
            return "---"
            
        hand = self._format_hand(raw_hero_cards)
        pos_name = position.name

        if pos_name not in self.charts:
            return f"No chart for {pos_name}"
            
        action = self.charts[pos_name].get(hand, "FOLD")
        return action