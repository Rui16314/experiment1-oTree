# experiment1/models.py
from otree.api import *
from random import randint, choice

class C(BaseConstants):
    NAME_IN_URL = 'experiment1'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 60  # 6 sessions × 10 rounds

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    price = models.CurrencyField(initial=cu(0))
    winner_id_in_group = models.IntegerField(initial=0)

class Player(BasePlayer):
    # Can be None until first used on Bid page; we will always set it before reading.
    valuation = models.CurrencyField()
    bid = models.CurrencyField(min=0, max=100, blank=True)

# -------- helper utilities --------
def phase_and_round_in_session(rn: int):
    """(session_no 1..6, round_in_session 1..10) for round_number rn"""
    s = (rn - 1) // 10 + 1
    r = (rn - 1) % 10 + 1
    return s, r

def rules_for_round(rn: int):
    s, _ = phase_and_round_in_session(rn)
    price = 'first' if s <= 3 else 'second'
    matching = 'random' if s in (1, 4) else 'fixed'
    chat = s in (3, 6)
    return dict(price=price, matching=matching, chat=chat)

def draw_valuation():
    # uniform 0–100, cents precision
    return cu(randint(0, 10000)) / 100

# -------- oTree hooks --------
def creating_session(subsession: Subsession):
    """Group players and assign valuations each round."""
    s_no, r_in_s = phase_and_round_in_session(subsession.round_number)
    r = rules_for_round(subsession.round_number)

    if r['matching'] == 'random':
        subsession.group_randomly()
    else:
        base = (s_no - 1) * 10 + 1
        if r_in_s == 1:
            subsession.group_randomly()
        else:
            subsession.group_like_round(base)

    # fresh valuation every round
    for p in subsession.get_players():
        p.valuation = draw_valuation()

def set_payoffs(group: Group):
    p1, p2 = group.get_players()
    b1 = p1.bid or cu(0)
    b2 = p2.bid or cu(0)

    if b1 > b2:
        winner, loser = p1, p2
    elif b2 > b1:
        winner, loser = p2, p1
    else:
        winner = choice([p1, p2])
        loser = p1 if winner is p2 else p2

    price_rule = rules_for_round(group.round_number)['price']
    price = (loser.bid or cu(0)) if price_rule == 'second' else (winner.bid or cu(0))

    group.price = price
    group.winner_id_in_group = winner.id_in_group

    # valuation may be None in legacy rows; guard with cu(0)
    winner.payoff = max(cu(0), (winner.valuation or cu(0)) - price)
    loser.payoff = cu(0)



