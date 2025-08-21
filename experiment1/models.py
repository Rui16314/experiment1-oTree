# experiment1/models.py
from otree.api import *  # Base*, cu, and models namespace


class C(BaseConstants):
    NAME_IN_URL = 'experiment1'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 10

    # knobs (can also be passed via session config)
    PRICE_RULE = 'first'   # 'first' or 'second'
    MATCHING   = 'random'  # 'random' or 'fixed'
    TIE_RULE   = 'random'  # how to break equal bids


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    price = models.CurrencyField(initial=0)
    winner_id_in_group = models.IntegerField(initial=0)


class Player(BasePlayer):
    valuation = models.CurrencyField(blank=True)          # set in creating_session
    bid       = models.CurrencyField(min=0, max=100, blank=True)  # may be None on timeout
    submitted = models.BooleanField(initial=False)


# ---------------- round setup ---------------- #

def creating_session(subsession: Subsession):
    """Group players and draw a valuation in [0, 100] each round."""
    import random

    if subsession.round_number == 1:
        subsession.group_randomly()
    else:
        if C.MATCHING == 'random':
            subsession.group_randomly()
        else:
            subsession.group_like_round(1)

    for p in subsession.get_players():
        # assign a valuation immediately so it won't be None later
        p.valuation = cu(round(random.uniform(0, 100), 2))


# -------------- outcome logic ---------------- #

def set_payoffs(group: Group):
    """Compute winner, price, and payoffs (first-price by default)."""

    import random

    p1, p2 = group.get_players()

    # SAFE reads that tolerate None
    v1 = p1.field_maybe_none('valuation') or cu(0)
    v2 = p2.field_maybe_none('valuation') or cu(0)
    b1 = p1.field_maybe_none('bid')
    b2 = p2.field_maybe_none('bid')

    # nobody bid
    if b1 is None and b2 is None:
        p1.payoff = cu(0)
        p2.payoff = cu(0)
        group.price = cu(0)
        group.winner_id_in_group = 0
        return

    # compare bids (treat None as -1 so the other wins)
    c1 = float(b1) if b1 is not None else -1
    c2 = float(b2) if b2 is not None else -1

    if c1 > c2:
        winner, loser = p1, p2
        v_w, v_l = v1, v2
        bw, bl = b1, b2
    elif c2 > c1:
        winner, loser = p2, p1
        v_w, v_l = v2, v1
        bw, bl = b2, b1
    else:
        # tie -> random winner
        winner = random.choice([p1, p2])
        loser  = p1 if winner is p2 else p2
        if winner is p1:
            v_w, v_l, bw, bl = v1, v2, b1, b2
        else:
            v_w, v_l, bw, bl = v2, v1, b2, b1

    # price rule
    if C.PRICE_RULE == 'first':
        price = bw or cu(0)
    else:
        price = bl or cu(0)  # second-price path (if you enable it later)

    group.price = price
    group.winner_id_in_group = winner.id_in_group

    winner.payoff = max(cu(0), v_w - price)
    loser.payoff  = cu(0)

