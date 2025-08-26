# experiment1/models.py
from otree.api import *
from random import randint, choice

class C(BaseConstants):
    NAME_IN_URL = 'experiment1'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 60
    ROUNDS_PER_SESSION = 10


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    price = models.CurrencyField(initial=cu(0))
    winner_id_in_group = models.IntegerField(initial=0)


class Player(BasePlayer):
    valuation = models.CurrencyField()
    bid = models.CurrencyField(min=0, max=100, blank=True)


# ---------------- helpers ----------------

def phase_and_round_in_session(rn: int):
    """returns (session_no 1..6, round_in_session 1..10)"""
    session_no = (rn - 1) // C.ROUNDS_PER_SESSION + 1
    round_in_session = (rn - 1) % C.ROUNDS_PER_SESSION + 1
    return session_no, round_in_session


def rules_for_round(rn: int):
    """Rules that apply in a given round."""
    s, _ = phase_and_round_in_session(rn)
    price_rule = 'first' if s <= 3 else 'second'
    matching = 'random' if s in (1, 4) else 'fixed'
    chat = s in (3, 6)
    return dict(price_rule=price_rule, matching=matching, chat=chat)


# --------------- oTree hooks ----------------

def creating_session(subsession: Subsession):
    """Group players & draw valuations each round."""
    s, ris = phase_and_round_in_session(subsession.round_number)
    r = rules_for_round(subsession.round_number)

    if r['matching'] == 'random':
        subsession.group_randomly()
    else:
        # fixed partner within the 10-round session block
        base_round = (s - 1) * C.ROUNDS_PER_SESSION + 1
        if ris == 1:
            subsession.group_randomly()          # choose pairs at start of session
        else:
            subsession.group_like_round(base_round)

    # fresh valuations every round
    for p in subsession.get_players():
        p.valuation = cu(randint(0, 10000)) / 100


def set_payoffs(group: Group):
    """Compute price & payoffs after both bids are in, defensively handling null bids."""
    p1, p2 = group.get_players()

    # IMPORTANT: use field_maybe_none to avoid the "null field" exception
    b1 = p1.field_maybe_none('bid')
    b2 = p2.field_maybe_none('bid')
    if b1 is None:
        b1 = cu(0)
    if b2 is None:
        b2 = cu(0)

    # winner/loser (break ties at random)
    if b1 > b2:
        winner, loser = p1, p2
    elif b2 > b1:
        winner, loser = p2, p1
    else:
        winner = choice([p1, p2])
        loser = p1 if winner is p2 else p2

    price_rule = rules_for_round(group.round_number)['price_rule']
    # again, get bid safely (may be None)
    wbid = winner.field_maybe_none('bid') or cu(0)
    lbid = loser.field_maybe_none('bid') or cu(0)
    price = lbid if price_rule == 'second' else wbid

    group.price = price
    group.winner_id_in_group = winner.id_in_group

    winner.payoff = max(cu(0), winner.valuation - price)
    loser.payoff = cu(0)



