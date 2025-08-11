from typing import Dict, Any
from acquisition.parser import Hand, Action


class StatsCalculator:
    STREETS = ('FLOP', 'TURN', 'RIVER')
    PO_POS = ('IP', 'OOP')
    POSITIONS = ('BB', 'SB', 'BTN', 'CO', 'MP', 'EP')

    def __init__(self, player_name: str):
        self.player = player_name

        # ─── Summary ───────────────────────────────────────────
        self.hands_played: int = 0
        self.total_bb_won: float = 0.0
        self.big_blind_size: float = 0.0
        self.current_stack: float = 0.0

        # ─── Preflop counters ──────────────────────────────────
        self.preflop = {k: 0 for k in ('vpip', 'pfr', 'fs', 'cpfr', 'uopfr', '3bet', '4bet' , 'f3b', 'f4b', 'sq', 'fsqr', 'fsqc')}
        #voluntarily put money in pot, preflop raise, flop seen, called preflop raise, unopened preflop raise, 3bet, 4bet, fold to 3 bet, fold to 4 bet, squeeze bet, fold to squeeze when raise, fold to squeeze when call 
        self.by_pos: Dict[int, Dict[str, int]] = {}

        self.steal = {k: 0 for k in ('bsa', 'fb', 'cs', 'rs', 'fr')}
        # blind steal attempts, fold to steal, called steal, resteal, fold to resteal
        self.steal_by_pos: Dict[int, Dict[str,int]] = {}

        self.postflop_street = {st : {k: 0 for k in ('bets', 'raises', 'calls', 'cr', 'fcr', 'cbet', 'fcb', 'rcb', 'frcb', 'cbet_3', 'fcb_3', 'db', 'fdb', 'cdb', 'wts', 'was', 'wws')} for st in self.STREETS}
        # bets, raises, calls, check raise, fold to check raise, cbet, fold to cbet, raise cbet, fold to raise cbet, cbet on 3bet, fold to cbet on 3bet, donk bet, fold to donk bet, call donk bet, went to showdown, won at showdown, won without showdown
        self.postflop_pos: Dict[str, Dict[str,int]] = {po: {'bets':0, 'raises':0, 'calls':0} for po in self.PO_POS}

    def _actor_order(self, hand: Hand):
        n = len(hand.players)
        return list(range(2, n+1)) + [1]

    def reset(self):
        self.__init__(self.player)

    def update_with_hand(self, hand: Hand):
        """Tally counters for this player from a parsed Hand."""
        if not self.big_blind_size:
            self.big_blind_size = float(hand.stakes.replace('$', '').split('/')[-1])
        for p in hand.players:
            if p.name == self.player:
                self.current_stack = p.stack
                won = hand.win_amounts.get(self.player, 0.0)
                self.total_bb_won += (won / self.big_blind_size)
                pos_id = p.pos_id or 1
                break

        self.hands_played += 1

        # preflop
        pf = [a for a in hand.actions if a.street == 'PREFLOP']

        self.by_pos.setdefault(pos_id, {'seen':0, 'vpip':0, 'pfr':0, '3bet':0})
        self.by_pos[pos_id]['seen'] += 1

        if any(a.player == self.player and a.action in ('calls', 'raises', 'bets') for a in pf):
            self.preflop['vpip'] += 1
            self.by_pos[pos_id]['vpip'] += 1

        if any(a.player == self.player and a.action == 'raises' for a in pf):
            self.preflop['pfr'] += 1
            self.by_pos[pos_id]['pfr'] += 1

        if hand.board['FLOP']:
            self.preflop['fs'] += 1

        if (any(a.player == self.player and a.action == 'calls' for a in pf) and any(a.action == 'raises' for a in pf)):
            self.preflop['cpfr'] += 1
        
        if (any(a.player == self.player and a.action == 'raises' for a in pf) and not any (a.player != self.player and a.action == 'raises' for a in pf)):
            self.preflop['uopfr'] += 1

        raises_all = [a for a in pf if a.action == 'raises']
        ours = [a for a in raises_all if a.player == self.player]

        if len(raises_all) >= 2 and ours:
            idx = raises_all.index(ours[0])
            if idx == 1:
                self.preflop['3bet'] += 1
                self.by_pos[pos_id]['3bet'] += 1
            elif idx == 2:
                self.preflop['4bet'] += 1

        if any(a.player == self.player and a.action == 'folds' for a in pf):
            if any(r for r in raises_all if raises_all.index(r) == 1 and r.player != self.player):
                self.preflop['f3b'] += 1
            if any(r for r in raises_all if raises_all.index(r) == 2 and r.player != self.player):
                self.preflop['f4b'] += 1

        if len(raises_all) == 2 and ours:
            self.preflop['sq'] += 1

        for a in pf:
            if a.player == self.player and a.action == 'folds':
                if len(raises_all) >= 2:
                    if not (len(raises_all) >= 3 and raises_all[2].player == self.player):
                        idx = [i for i, x in enumerate(pf) if x.player == self.player and x.action == 'folds'][0]
                        i2 = pf.index(raises_all[1])
                        if idx>i2:
                            self.preflop['fsqr'] += 1
                if len(raises_all) >= 3 and raises_all[2].player == self.player:
                    self.preflop['fsqc'] += 1

        # steal
        if pos_id in (1,2):
            if any(a.player == self.player and a.action == 'raises' for a in pf):
                self.steal['bsa'] += 1
                self.steal_by_pos.setdefault(pos_id, {'bsa':0, 'fb':0, 'cs':0, 'rs':0, 'fr':0})
                self.steal_by_pos[pos_id]['bsa'] += 1
            if any(a.player == self.player and a.action == 'folds' for a in pf):
                if any(a.action == 'raises' and a.player != self.player for a in pf):
                    self.steal['fb'] += 1
                    self.steal_by_pos[pos_id]['fb'] += 1
            if any(a.player == self.player and a.action == 'calls' for a in pf) and not any(x.action == 'posts' for x in pf if x.player == self.player):
                if any(a.action == 'raises' and a.player != self.player for a in pf):
                    self.steal['cs'] += 1
                    self.steal_by_pos[pos_id]['cs'] = self.steal_by_pos.get(pos_id, {}).get('cs', 0) + 1
            if any(a.action == self.player and a.action == 'raises' for a in pf) and any(x.action == 'raises' and x.player != self.player for x in pf):
                self.steal['rs'] += 1
                self.steal_by_pos[pos_id]['rs'] = self.steal_by_pos.get(pos_id, {}).get('fr', 0) + 1
            if any(a.player == self.player and a.action == 'folds' for a in pf) and len([x for x in pf if x.action == 'raises']) >= 2:
                self.steal['fr'] += 1
                self.steal_by_pos[pos_id]['fr'] = self.steal_by_pos.get(pos_id, {}).get('fr', 0) + 1
        
        # postflop
        pf_aggs = [a for a in pf if a.action in ('bets', 'raises')]
        last_pf_agg = pf_aggs[-1].player if pf_aggs else None
        pf_3bpot = len(raises_all) >= 2

        actor_order = self._actor_order(hand)

        for st in self.STREETS:
            st_acts = [a for a in hand.actions if a.street == st]

            st_aggs = [a for a in st_acts if a.action in ('bets', 'raises')]
            for idx, a in enumerate(st_acts):
                if a.player != self.player:
                    continue

                prev_aggs = [x for x in st_aggs if st_acts.index(x) < idx]
                last_agg = prev_aggs[-1] if prev_aggs else None

                if last_agg:
                    me_idx = actor_order.index(p.pos_idx)
                    la_idx = actor_order.index(last_agg.pos_id)
                    po = 'IP' if me_idx > la_idx else 'OOP'
                else:
                    po = 'IP'
                self.postflop_pos[po][a.action] += 1

                self.postflop_street[st][a.action] += 1 

                if a.action == 'raises':
                    my_acts = [x for x in st_acts if x.player == self.player]
                    if any(x.action == 'checks' for x in my_acts):
                        self.postflop_street[st]['cr'] += 1

                if a.action == 'folds' and last_agg and last_agg.action == 'raises':
                    op_acts = [x for x in st_acts if x.player == last_agg.player]
                    if any(x.action == 'checks' for x in op_acts[:op_acts.index(last_agg)]):
                        self.postflop_street[st]['fcr'] += 1
                
                if st == 'FLOP' and a.action == 'bets' and last_pf_agg == self.player:
                    self.postflop_street[st]['cbet'] += 1
                    if pf_3bpot:
                        self.postflop_street[st]['cbet3'] += 1

                if st == 'FLOP' and a.action == 'folds' and last_agg and last_agg.player != self.player and last_agg.action == 'bets' and last_pf_agg == self.player:
                    self.postflop_street[st]['fcb'] += 1
                    if pf_3bpot:
                        self.postflop_street[st]['fcb3'] += 1

                if st=='FLOP' and a.action=='raises' and last_agg and last_pf_agg==self.player and last_agg.player!=self.player and last_agg.action=='bets':
                    self.postflop_street[st]['rcb'] +=1

                if st=='FLOP' and a.action=='folds' and last_agg and last_pf_agg==self.player and last_agg.player!=self.player and last_agg.action=='raises':
                    self.postflop_street[st]['frcb'] +=1

                if a.action=='bets' and last_pf_agg!=self.player and not prev_aggs:
                    self.postflop_street[st]['donk'] +=1

                if a.action=='folds' and last_agg and last_pf_agg!=self.player and last_agg.action=='bets':
                    self.postflop_street[st]['fdb'] +=1

                if a.action=='calls' and last_agg and last_pf_agg!=self.player and last_agg.action=='bets':
                    self.postflop_street[st]['cdb'] +=1

            if self.player in hand.showdown:
                self.postflop_street[st]['wts'] +=1
                if self.player in hand.winners:
                    self.postflop_street[st]['was'] +=1
            elif self.player in hand.winners:
                self.postflop_street[st]['wws'] +=1

    def compute_stats(self) -> Dict[str,Any]:
        """Return nested stats for GUI consumption."""
        hp = max(self.hands_played,1)

        pf_ov = {
            'VPIP%':  self.preflop['vpip']/hp*100,
            'PFR%':   self.preflop['pfr']/hp*100,
            'FS%':    self.preflop['fs']/hp*100,
            'CPFR%':  self.preflop['cpfr']/hp*100,
            'UOPR%':  self.preflop['uopr']/hp*100,
            '3B%':    self.preflop['3bet']/hp*100,
            '4B%':    self.preflop['4bet']/hp*100,
        }
        pf_bp = {
            pos: {
                'Seen': self.by_pos[pos]['seen'],
                'VPIP%': self.by_pos[pos]['vpip']/max(self.by_pos[pos]['seen'],1)*100,
                'PFR%':  self.by_pos[pos]['pfr']/max(self.by_pos[pos]['seen'],1)*100,
                '3B%':   self.by_pos[pos]['3bet']/max(self.by_pos[pos]['seen'],1)*100,
            }
            for pos in sorted(self.by_pos)
        }

        st_ov = {
            'BSA%': self.steal['bsa']/hp*100,
            'FB%':  self.steal['fb']/hp*100,
            'CS%':  self.steal['cs']/hp*100,
            'RS%':  self.steal['rs']/hp*100,
            'FR%':  self.steal['fr']/hp*100,
        }
        st_bp = {
            pos: {
                'BSA%': self.steal_by_pos[pos]['bsa']/hp*100,
                'FB%':  self.steal_by_pos[pos]['fb']/hp*100,
                'CS%':  self.steal_by_pos[pos].get('cs',0)/hp*100,
                'RS%':  self.steal_by_pos[pos].get('rs',0)/hp*100,
                'FR%':  self.steal_by_pos[pos].get('fr',0)/hp*100,
            }
            for pos in sorted(self.steal_by_pos)
        }

        tot_b = sum(self.postflop_street[s]['bets']   for s in self.STREETS)
        tot_r = sum(self.postflop_street[s]['raises'] for s in self.STREETS)
        tot_c = sum(self.postflop_street[s]['calls']  for s in self.STREETS)

        pf_overall = {
            'Agg%': (tot_b+tot_r)/tot_c*100 if tot_c else 0,
            'AF':   (tot_b+tot_r)/tot_c     if tot_c else 0,
            'WTS%': sum(self.postflop_street[s]['wts'] for s in self.STREETS)/hp*100,
            'WAS%': sum(self.postflop_street[s]['was'] for s in self.STREETS)/hp*100,
            'WWS%': sum(self.postflop_street[s]['wws'] for s in self.STREETS)/hp*100,
        }

        pf_bs = {
            st: {
                'Bet%':   self.postflop_street[st]['bets']/hp*100,
                'Raise%': self.postflop_street[st]['raises']/hp*100,
                'Call%':  self.postflop_street[st]['calls']/hp*100,
                'CR%':    self.postflop_street[st]['cr']/hp*100,
                'FCR%':   self.postflop_street[st]['fcr']/hp*100,
                'CBet%':  self.postflop_street[st]['cbet']/hp*100,
                'FCB%':   self.postflop_street[st]['fcb']/hp*100,
                'RCB%':   self.postflop_street[st]['rcb']/hp*100,
                'FRCB%':  self.postflop_street[st]['frcb']/hp*100,
                'CBet3%': self.postflop_street[st]['cbet3']/hp*100,
                'FCB3%':  self.postflop_street[st]['fcb3']/hp*100,
                'DB%':    self.postflop_street[st]['donk']/hp*100,
                'FDB%':   self.postflop_street[st]['fdb']/hp*100,
                'CDB%':   self.postflop_street[st]['cdb']/hp*100,
            }
            for st in self.STREETS
        }

        pf_ip = {
            po: {
                'Bet%':   self.postflop_pos[po]['bets']/hp*100,
                'Raise%': self.postflop_pos[po]['raises']/hp*100,
                'Call%':  self.postflop_pos[po]['calls']/hp*100,
            }
            for po in self.PO_POS
        }

        return {
            'Preflop':  {'overall': pf_ov, 'by_pos': pf_bp},
            'Steal':    {'overall': st_ov, 'by_pos': st_bp},
            'Postflop': {
                'overall':   pf_overall,
                'by_street': pf_bs,
                'by_ip_oop': pf_ip
            }
        }


            



class StatsManager:
    """
    one for each player
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
        return {
            name: calc.compute_stats()
            for name, calc in self.by_player.items()
        }
