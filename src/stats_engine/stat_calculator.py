from typing import Dict, Any, List
from acquisition.parser import Hand, Action, Player


class StatsCalculator:
    """
    Tracks all raw counters for a single player, then computes
    VPIP, PFR, FS, 3-bet, 4-bet, steals, postflop aggression, etc.
    """
    POSITIONS = ('BB', 'SB', 'BTN', 'CO', 'MP', 'EP')

    def __init__(self, player_name: str):
        self.player = player_name

        # ─── Summary ───────────────────────────────────────────
        self.hands_played: int = 0
        self.total_bb_won: float = 0.0
        self.big_blind_size: float = 0.0
        self.current_stack: float = 0.0

        # ─── Preflop counters ──────────────────────────────────
        self.preflop = {
            'vpip': 0,      # voluntarily put money in pot
            'pfr': 0,       # preflop raise
            'fs': 0,        # flop seen
            'cpfr': 0,      # called preflop raise
            'uopr': 0,      # unopened preflop raise
            '3bet': 0,
            '4bet': 0,
            'f3b': 0,       # folded to 3-bet
            'f4b': 0,       # folded to 4-bet
            'sq': 0,        # squeeze bet
            'fsqr': 0,      # folded to squeeze
            'fsqc': 0,      # called squeeze
        }

        # ─── Steal counters ────────────────────────────────────
        self.steal = {
            'bsa': 0,       # blind steal attempts
            'fb': 0,        # folded to steal
            'cs': 0,        # cold call steal
            'rs': 0,        # re-steal attempts
            'fr': 0,        # folded to re-steal
        }

        # ─── Postflop counters ─────────────────────────────────
        self.postflop = {
            'agg_bets': 0,      # total bets + raises
            'calls': 0,
            'bets': 0,
            'raises': 0,
            'cr': 0,            # check-raises
            'fcr': 0,           # folded to check-raise
            'cbet': 0,          # continuation bets
            'fcb': 0,           # folded to continuation bet
            'rcb': 0,           # raised continuation bet
            'frcb': 0,          # folded to raised cbet
            'cbet3': 0,         # cbet on flop in 3-bet pot
            'fcb3': 0,          # folded to cbet on flop in 3-bet pot
            'donk': 0,          # donk bets
            'fdb': 0,           # folded to donk bet
            'cdb': 0,           # called donk bet
            'wts': 0,           # went to showdown
            'was': 0,           # won at showdown
            'wws': 0,           # won without showdown
        }

        # ─── Position heatmap ──────────────────────────────────
        # Track how often we see each position and take VPIP/PFR/3B there
        self.by_pos: Dict[str, Dict[str, int]] = {
            pos: {'seen': 0, 'vpip': 0, 'pfr': 0, '3bet': 0}
            for pos in self.POSITIONS
        }

    def reset(self):
        self.__init__(self.player)

    def update_with_hand(self, hand: Hand):
        """Tally counters for this player from a parsed Hand."""
        # 1) initialize BB size & stack info
        if not self.big_blind_size:
            # stakes format e.g. "$0.05/$0.10" or "0.05/0.10"
            parts = hand.stakes.replace('$', '').split('/')
            self.big_blind_size = float(parts[-1])
        # find this player's seat & resulting stack (from summary)
        for p in hand.players:
            if p.name == self.player:
                self.current_stack = p.stack
                break

        self.hands_played += 1

        # 2) SUMMARY: compute BB won this hand
        #    TODO: parse the actual collected amount from Hand summary
        # self.total_bb_won += (amount_collected / self.big_blind_size)

        # 3) POSITION: record which position we were in
        pos = None
        for p in hand.players:
            if p.name == self.player:
                pos = p.position  # parser should fill 'SB','BB', etc.
        if pos in self.by_pos:
            self.by_pos[pos]['seen'] += 1

        # 4) PRE-FLOP
        pf_actions = [a for a in hand.actions if a.street == 'PREFLOP']
        # VPIP: any voluntary call/raise/bet (excluding blinds)
        if any(a.player == self.player and a.action in ('calls','raises','bets')
               for a in pf_actions):
            self.preflop['vpip'] += 1
            if pos in self.by_pos:
                self.by_pos[pos]['vpip'] += 1
        # PFR: any raise
        if any(a.player == self.player and a.action == 'raises'
               for a in pf_actions):
            self.preflop['pfr'] += 1
            if pos in self.by_pos:
                self.by_pos[pos]['pfr'] += 1
        # FS: saw the flop?
        if hand.board['FLOP']:
            self.preflop['fs'] += 1
        # CPFR: called after someone raised preflop
        if any(a.player == self.player and a.action == 'calls'
               for a in pf_actions) and any(a.action == 'raises' for a in pf_actions):
            self.preflop['cpfr'] += 1
        # UOPR: first raise (open raise)
        if (any(a.player == self.player and a.action == 'raises' for a in pf_actions)
            and not any(a.action == 'raises' for a in pf_actions if a.player != self.player)):
            self.preflop['uopr'] += 1
        # 3-bet & 4-bet detection
        raises = [a for a in pf_actions if a.action == 'raises']
        our_raises = [a for a in raises if a.player == self.player]
        if len(raises) >= 2 and our_raises:
            # crude: if we are second raiser => 3-bet
            if raises.index(our_raises[0]) == 1:
                self.preflop['3bet'] += 1
                if pos in self.by_pos:
                    self.by_pos[pos]['3bet'] += 1
            # if we are third raiser => 4-bet
            if raises.index(our_raises[0]) == 2:
                self.preflop['4bet'] += 1
        # F3B/F4B: folded to 3-bet/4-bet
        if any(a.player == self.player and a.action == 'folds' for a in pf_actions):
            # if there's been a 3-bet before our fold
            if any(r for r in raises if raises.index(r) == 1 and r.player != self.player):
                self.preflop['f3b'] += 1
            if any(r for r in raises if raises.index(r) == 2 and r.player != self.player):
                self.preflop['f4b'] += 1
        # Squeeze: we raise after a limp + raise
        if len(raises) == 2 and our_raises:
            self.preflop['sq'] += 1
        # Fold/Call to squeeze
        # TODO: detect if the raise was a squeeze, then track fsqr, fsqc

        # 5) STEALS (typically from SB/BTN vs only blinds)
        # TODO: refine definition: a raise from SB/BTN when no other callers
        preflop_posters = [a for a in pf_actions if a.action.startswith('posts')]
        if pos in ('SB','BTN') and any(a.player == self.player and a.action == 'raises'
                                         for a in pf_actions):
            self.steal['bsa'] += 1
        if any(a.player == self.player and a.action == 'folds' for a in pf_actions
               ) and any(a.action == 'raises' for a in pf_actions if a.player != self.player):
            self.steal['fb'] += 1
        # TODO: detect cold-call vs steal (cs), re-steal (rs), fold to re-steal (fr)

        # 6) POST-FLOP
        for street in ('FLOP','TURN','RIVER'):
            street_actions = [a for a in hand.actions if a.street == street]
            for a in street_actions:
                if a.player != self.player:
                    continue
                if a.action == 'bets':
                    self.postflop['bets'] += 1
                if a.action == 'raises':
                    self.postflop['raises'] += 1
                if a.action == 'calls':
                    self.postflop['calls'] += 1
                if a.action == 'checks' and any(
                    b for b in street_actions if b.action in ('bets','raises')
                ):
                    # we faced a bet and checked => folded to c-r
                    self.postflop['fcr'] += 1
                # Check-raise
                # TODO: detect check-raise sequence (cr)
            # continuation bet on flop
            if street == 'FLOP':
                # if we were the last aggressor preflop and we bet flop
                if any(a.player == self.player and a.action == 'bets'
                       for a in street_actions):
                    self.postflop['cbet'] += 1
            # donk bets: bet when not last aggressor
            # TODO

        # Showdown & wins
        if hand.showdown.get(self.player):
            self.postflop['wts'] += 1
            if self.player in hand.winners:
                self.postflop['was'] += 1
        else:
            # if we collected without showdown
            if self.player in hand.winners:
                self.postflop['wws'] += 1

    def compute_stats(self) -> Dict[str, Any]:
        """Compute derived percentages, ratios, and per-100-hand figures."""
        hp = max(self.hands_played, 1)
        calls = self.postflop['calls']
        bets = self.postflop['bets']
        raises = self.postflop['raises']

        out: Dict[str, Any] = {
            # Summary
            'Hands': self.hands_played,
            'TBB/100': (self.total_bb_won / hp) * 100,
            'M': (self.current_stack / (self.big_blind_size * 2)) if self.big_blind_size else 0,
            'BB_remain': (self.current_stack / self.big_blind_size) if self.big_blind_size else 0,
            # Preflop
            'VPIP%': self.preflop['vpip'] / hp * 100,
            'PFR%': self.preflop['pfr'] / hp * 100,
            'FS%': self.preflop['fs'] / hp * 100,
            'CPFR%': self.preflop['cpfr'] / hp * 100,
            'UOPR%': self.preflop['uopr'] / hp * 100,
            '3B%': self.preflop['3bet'] / hp * 100,
            '4B%': self.preflop['4bet'] / hp * 100,
            'F3B%': self.preflop['f3b'] / hp * 100,
            'F4B%': self.preflop['f4b'] / hp * 100,
            'Sq%': self.preflop['sq'] / hp * 100,
            # Steal
            'BSA%': self.steal['bsa'] / hp * 100,
            'FB%': self.steal['fb'] / hp * 100,
            # Postflop
            'Agg%': (bets + raises) / calls * 100 if calls else None,
            'AF': (bets + raises) / calls if calls else None,
            'CR%': self.postflop['cr'] / hp * 100,
            'FCR%': self.postflop['fcr'] / hp * 100,
            'CBet%': self.postflop['cbet'] / hp * 100,
            'FCB%': self.postflop['fcb'] / hp * 100,
            'RCB%': self.postflop['rcb'] / hp * 100,
            'FRCB%': self.postflop['frcb'] / hp * 100,
            'Donk%': self.postflop['donk'] / hp * 100,
            'FDB%': self.postflop['fdb'] / hp * 100,
            'CDB%': self.postflop['cdb'] / hp * 100,
            'WTS%': self.postflop['wts'] / hp * 100,
            'WAS%': self.postflop['was'] / hp * 100,
            'WWS%': self.postflop['wws'] / hp * 100,
            # Positional breakdown
            'ByPos': {
                pos: {
                    'Seen': self.by_pos[pos]['seen'],
                    'VPIP%': self.by_pos[pos]['vpip'] / max(self.by_pos[pos]['seen'], 1) * 100,
                    'PFR%':  self.by_pos[pos]['pfr'] / max(self.by_pos[pos]['seen'], 1) * 100,
                    '3B%':   self.by_pos[pos]['3bet'] / max(self.by_pos[pos]['seen'], 1) * 100,
                }
                for pos in self.POSITIONS
            }
        }
        return out


class StatsManager:
    """
    Holds one StatsCalculator per player. On each new Hand,
    ensures calculators exist and updates all of them, then
    can compute each player’s stat dictionary.
    """
    def __init__(self):
        self.by_player: Dict[str, StatsCalculator] = {}

    def update_with_hand(self, hand: Hand):
        # ensure every seat has a calculator
        for pl in hand.players:
            if pl.name not in self.by_player:
                self.by_player[pl.name] = StatsCalculator(pl.name)
        # update each
        for calc in self.by_player.values():
            calc.update_with_hand(hand)

    def compute_all(self) -> Dict[str, Any]:
        """
        Returns:
            { player_name: { stat_name: value, ... }, ... }
        """
        return {
            name: calc.compute_stats()
            for name, calc in self.by_player.items()
        }
