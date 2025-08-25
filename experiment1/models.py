# experiment1/models.py
from otree.api import *
from random import randint, choice


class C(BaseConstants):
    NAME_IN_URL = 'experiment1'
    PLAYERS_PER_GROUP = 2
    # 6 sessions × 10 rounds = 60 total rounds
    ROUNDS_PER_SESSION = 10
    NUM_ROUNDS = 6 * ROUNDS_PER_SESSION


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    price = models.CurrencyField()
    winner_id_in_group = models.IntegerField(initial=0)


class Player(BasePlayer):
    valuation = models.CurrencyField()
    bid = models.CurrencyField(min=0, max=100, blank=True)


# ---------------- helpers ----------------

def draw_valuation() -> currency:
    # uniform 0–100 with two decimals
    return cu(randint(0, 10000)) / 100


def session_and_within_round(rn: int):
    """(session_no 1..6, round_in_session 1..10) from absolute round number"""
    s_no = (rn - 1) // C.ROUNDS_PER_SESSION + 1
    r_in = (rn - 1) % C.ROUNDS_PER_SESSION + 1
    return s_no, r_in


def rules_for_round(rn: int):
    """First 3 sessions = first-price; last 3 = second-price.
       1 & 4 random matching; 2 & 5 fixed; 3 & 6 fixed+chat."""
    s_no, _ = session_and_within_round(rn)
    price = 'first' if s_no <= 3 else 'second'
    matching = 'random' if s_no in (1, 4) else 'fixed'
    chat = s_no in (3, 6)
    return dict(price=price, matching=matching, chat=chat)


def creating_session(subsession: Subsession):
    # grouping per round
    s_no, r_in = session_and_within_round(subsession.round_number)
    r = rules_for_round(subsession.round_number)

    if r['matching'] == 'random':
        subsession.group_randomly()
    else:
        first_round_of_this_session = (s_no - 1) * C.ROUNDS_PER_SESSION + 1
        if r_in == 1:
            subsession.group_randomly()               # choose pairs at session start
        else:
            subsession.group_like_round(first_round_of_this_session)

    # assign valuation for everyone, every round
    for p in subsession.get_players():
        p.valuation = draw_valuation()


def set_payoffs(group: Group):
    p1, p2 = group.get_players()
    b1 = p1.bid if p1.bid is not None else cu(0)
    b2 = p2.bid if p2.bid is not None else cu(0)

    if b1 > b2:
        winner, loser = p1, p2
    elif b2 > b1:
        winner, loser = p2, p1
    else:
        winner = choice([p1, p2])
        loser = p1 if winner is p2 else p2

    price_rule = rules_for_round(group.round_number)['price']
    price = loser.bid if price_rule == 'second' else winner.bid

    group.price = price
    group.winner_id_in_group = winner.id_in_group
    winner.payoff = max(cu(0), winner.valuation - price)
    loser.payoff = cu(0)


