# experiment1/models.py
from otree.api import *
import random


class C(BaseConstants):
    NAME_IN_URL = 'experiment1'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 60               # 6 sessions × 10 rounds
    ROUNDS_PER_SESSION = 10


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    price = models.CurrencyField()
    winner_id_in_group = models.IntegerField()


class Player(BasePlayer):
    valuation = models.CurrencyField()
    bid = models.CurrencyField(min=0, max=100, blank=True)


# ---------- helpers about session/round and rules ----------

def session_and_round(rn: int):
    """returns (session_no 1..6, round_in_session 1..10)"""
    s_no = (rn - 1) // C.ROUNDS_PER_SESSION + 1
    r_in_s = (rn - 1) % C.ROUNDS_PER_SESSION + 1
    return s_no, r_in_s


def rules_for_round(rn: int):
    """Rules for a given round number."""
    s_no, _ = session_and_round(rn)
    return dict(
        price=('first' if s_no <= 3 else 'second'),
        matching=('random' if s_no in (1, 4) else 'fixed'),
        chat=(s_no in (3, 6)),
    )


def draw_valuation():
    # uniform 0–100 (in cents), returned as Currency
    return cu(random.randint(0, 10000)) / 100


# ---------- oTree hooks ----------

def creating_session(subsession: Subsession):
    """Group players & draw valuations each round."""
    s_no, r_in_s = session_and_round(subsession.round_number)
    r = rules_for_round(subsession.round_number)

    # grouping
    if r['matching'] == 'random':
        subsession.group_randomly()
    else:
        base_round = (s_no - 1) * C.ROUNDS_PER_SESSION + 1
        if r_in_s == 1:
            subsession.group_randomly()          # choose pairs at start of session block
        else:
            subsession.group_like_round(base_round)

    # assign valuations for this round
    for p in subsession.get_players():
        p.valuation = draw_valuation()


def set_payoffs(group: Group):
    """Compute price & payoffs after both bids are in."""
    p1, p2 = group.get_players()
    b1 = p1.bid or cu(0)
    b2 = p2.bid or cu(0)

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



