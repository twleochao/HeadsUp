import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class Player:
    seat: int
    name: str
    stack: float 
    pos_id: Optional[int] = None

@dataclass
class Action:
    street: str
    player: str
    action: str
    amount: Optional[float] = None

@dataclass
class Hand:
    hand_id: str
    date: str
    table: str
    button_seat: int
    stakes: str
    players: List[Player] = field(default_factory=list)
    posts: List[Action] = field(default_factory=list)
    hole_cards: Dict[str, List[str]] = field(default_factory=dict)
    actions: List[Action] = field(default_factory=list)
    board: Dict[str, List[str]] = field(default_factory=lambda: {'FLOP': [], 'TURN': [], 'RIVER': []})
    showdown: Dict[str, List[str]] = field(default_factory=dict)
    winners: List[str] = field(default_factory=list)
    win_amounts: Dict[str, float] = field(default_factory=dict)



def parse_hand(hand_text: str) -> Hand:
    # Split lines and initialize
    lines = hand_text.strip().splitlines()
    header = lines[0]

    # Regex patterns
    header_re = re.compile(r"PokerStars Hand #(?P<id>\d+):(?: Tournament #(?P<tour>\d+), )? (?P<stakes>[^-]+)- (?P<date>.+)")
    table_re = re.compile(r"Table '(?P<table>[^']+)' \d+-max Seat #(?P<button>\d+) is the button")
    seat_re = re.compile(r"Seat (?P<seat>\d+): (?P<name>\S+) \(?\$?(?P<stack>[\d\.]+) in chips\)?")
    post_re = re.compile(r"(?P<player>\S+): posts (?:small blind|big blind|the ante|small blind|big blind) ?(?P<amount>[\d\.]+)")
    # Note: ante, sb, bb all captured
    dealt_re = re.compile(r"Dealt to (?P<player>\S+) \[(?P<cards>[\w\s]+)\]")
    street_re = re.compile(r"\*\*\* (?P<street>HOLE CARDS|FLOP|TURN|RIVER) \*\*\*(?: \[(?P<cards>[\w\s]+)\])?")
    action_re = re.compile(r"(?P<player>\S+): (?P<action>folds|checks|calls|bets|raises)(?: (?P<amount>[\d\.]+)(?: to (?P<to>[\d\.]+))?)?")
    showdown_re = re.compile(r"(?P<player>\S+): shows \[(?P<cards>[\w\s]+)\]")
    win_re = re.compile(r"(?P<player>\S+) (?:collected|wins) \$?(?P<amount>[\d\.]+)")

    # Parse header
    m = header_re.match(header)
    if not m:
        raise ValueError(f"Invalid hand header: {header}")

    hand = Hand(
        hand_id=m.group('id'),
        stakes=m.group('stakes').strip(),
        date=m.group('date').strip(),
        table='',
        button_seat=0
    )

    # Parse table/button
    m = table_re.match(lines[1])
    hand.table = m.group('table')
    hand.button_seat = int(m.group('button'))

    # State machine
    street = 'PREFLOP'
    for line in lines[2:]:
        # Seats
        if (m := seat_re.match(line)):
            hand.players.append(Player(seat=int(m.group('seat')), name=m.group('name'), stack=float(m.group('stack'))))
            continue
        # Posts
        if (m := post_re.match(line)):
            hand.posts.append(Action(street='PREFLOP', player=m.group('player'), action='posts', amount=float(m.group('amount'))))
            continue
        # Dealt
        if (m := dealt_re.match(line)):
            hand.hole_cards[m.group('player')] = m.group('cards').split()
            continue

        # New Street
        if (m := street_re.match(line)):
            raw = m.group('street')
            if raw == 'HOLE CARDS':
                street = 'PREFLOP'
            else:
                street = raw
                cards = m.group('cards')
                if cards:
                    hand.board[street] = cards.split()
            continue

        # Actions
        if (m := action_re.match(line)):
            amt = None
            if m.group('to'):
                amt = float(m.group('to'))
            elif m.group('amt'):
                amt = float(m.group('amt'))
            hand.actions.append(Action(street=street, player=m.group('player'), action=m.group('action'), amout=amt))
            continue
            
        # Showdown
        if (m := showdown_re.match(line)):
            hand.showdown[m.group('player')] = m.group('cards').split()
            continue

        # Wins
        if (m := win_re.match(line)):
            player = m.group('player')
            amt = float(m.group('amount'))
            hand.win_amounts[player] = amt
            hand.winners.append(player)
            continue

    
    # position assignment
    seats = sorted(p.seat for p in hand.players)
    n = len(seats)
    btn_idx = seats.index(hand.button_seat)
    for p in hand.players:
        idx = seats.index(p.seat)
        rel = (idx - btn_idx) % n
        p.pos_id = rel + 1

    return hand
