# experiment1/models.py
from otree.api import *
import random


class C(BaseConstants):
    NAME_IN_URL = 'experiment1'
    PLAYERS_PER_GROUP = 2
    # 6 sessions × 10 rounds each
    NUM_ROUNDS = 60


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    price = models.CurrencyField(initial=cu(0))
    winner_id_in_group = models.IntegerField(initial=0)


class Player(BasePlayer):
    # use integer points 0..100 to keep it simple & robust
    valuation = models.CurrencyField()
    bid = models.CurrencyField(min=0, max=100, blank=True)


# ---------- helpers ----------

def phase_and_round_in_session(rn: int):
    """Return (session_no 1..6, round_in_session 1..10)."""
    session_no = (rn - 1) // 10 + 1
    round_in_session = (rn - 1) % 10 + 1
    return session_no, round_in_session


def rules_for_round(rn: int):
    """Which rules apply in this round?"""
    s, _ = phase_and_round_in_session(rn)
    price = 'first' if s <= 3 else 'second'
    matching = 'random' if s in (1, 4) else 'fixed'
    chat = s in (3, 6)
    return dict(price=price, matching=matching, chat=chat)


def draw_valuation():
    # robust: integer 0..100 (no float issues)
    return cu(random.randint(0, 100))


# ---------- oTree hooks ----------

def creating_session(subsession: Subsession):
    """Group players & draw valuations each round."""
    s_no, r_in_s = phase_and_round_in_session(subsession.round_number)
    r = rules_for_round(subsession.round_number)

    if r['matching'] == 'random':
        subsession.group_randomly()
    else:
        # fixed partner within the 10-round session block
        base_round = (s_no - 1) * 10 + 1
        if r_in_s == 1:
            subsession.group_randomly()          # choose pairs at start of session
        else:
            subsession.group_like_round(base_round)

    for p in subsession.get_players():
        # ensure valuation exists every round
        p.valuation = draw_valuation()


def set_payoffs(group: Group):
    """Set winner, price, payoffs after both bids are in."""
    p1, p2 = group.get_players()
    b1 = p1.bid if p1.bid is not None else cu(0)
    b2 = p2.bid if p2.bid is not None else cu(0)

    # determine winner (break ties at random)
    if b1 > b2:
        winner, loser = p1, p2
    elif b2 > b1:
        winner, loser = p2, p1
    else:
        winner = random.choice([p1, p2])
        loser = p1 if winner is p2 else p2

    price_rule = rules_for_round(group.round_number)['price']
    price = loser.bid if price_rule == 'second' else winner.bid

    group.price = price
    group.winner_id_in_group = winner.id_in_group

    winner.payoff = max(cu(0), winner.valuation - price)
    loser.payoff = cu(0)


