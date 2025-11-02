import os
import json
from src.core.datatypes import Position

STUB_RFI_CHARTS = {}

class PreflopSolver:
    def __init__(self, chart_path: str = None):
        """
        Initializes the solver.
        If chart_path is provided, loads charts from disk.
        Otherwise, uses the stub charts.
        """
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
        """
        The main lookup function.
        
        TODO: This is a simple RFI (Raise First In) lookup.
        We will need to expand this to handle "vs 3-bet", "vs open", etc.
        """
        if not raw_hero_cards or position == Position.UNKNOWN:
            return "---"
            
        hand = self._format_hand(raw_hero_cards)
        pos_name = position.name

        if pos_name not in self.charts:
            return f"No chart for {pos_name}"
            
        action = self.charts[pos_name].get(hand, "FOLD")
        return action