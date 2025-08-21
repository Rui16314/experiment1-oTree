# experiment1/models.py
from otree.api import (
    Currency as cu, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    CurrencyField, IntegerField, BooleanField
)
import random  # <-- make sure this import is present

class C(BaseConstants):
    NAME_IN_URL = 'experiment1'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 10
    PRICE_RULE = 'first'
    MATCHING   = 'random'
    TIE_RULE   = 'random'

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    price = CurrencyField(initial=0)
    winner_id_in_group = IntegerField(initial=0)

    # NEW: set valuations for all players in this group at the start of each round
    def assign_valuations(self):
        for p in self.get_players():
            # 0–100 integer points works cleanly with CurrencyField/cu
            p.valuation = cu(random.randint(0, 100))

class Player(BasePlayer):
    valuation = CurrencyField()
    bid = CurrencyField(min=0, max=100, blank=True)
    submitted = BooleanField(initial=True)

# (keep your existing set_payoffs exactly as you already have it)
def set_payoffs(group: Group):
    import random
    p1, p2 = group.get_players()
    b1, b2 = p1.bid, p2.bid
    c1 = float(b1) if b1 is not None else -1
    c2 = float(b2) if b2 is not None else -1

    if b1 is None and b2 is None:
        p1.payoff = cu(0); p2.payoff = cu(0)
        group.price = cu(0); group.winner_id_in_group = 0
        return

    if c1 > c2:
        winner, loser = p1, p2
    elif c2 > c1:
        winner, loser = p2, p1
    else:
        winner = random.choice([p1, p2]); loser = p1 if winner is p2 else p2

    price = winner.bid if C.PRICE_RULE == 'first' else (loser.bid if loser.bid is not None else cu(0))
    group.price = price
    group.winner_id_in_group = winner.id_in_group
    winner.payoff = max(cu(0), winner.valuation - price)
    loser.payoff = cu(0)
