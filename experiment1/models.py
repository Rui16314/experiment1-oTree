# experiment1/models.py
from otree.api import *  # brings in Base*, cu, and the models namespace


class C(BaseConstants):
    NAME_IN_URL = 'experiment1'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 10

    # knobs (can also be passed via session config)
    PRICE_RULE = 'first'   # 'first' or 'second' (we use first-price here)
    MATCHING = 'random'    # 'random' or 'fixed'
    TIE_RULE = 'random'    # how to break equal bids


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    price = models.CurrencyField(initial=0)
    winner_id_in_group = models.IntegerField(initial=0)


class Player(BasePlayer):
    valuation = models.CurrencyField(blank=True)                 # set each round
    bid = models.CurrencyField(min=0, max=100, blank=True)       # may be None on timeout
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
        p.valuation = cu(round(random.uniform(0, 100), 2))


# -------------- outcome logic ---------------- #

def set_payoffs(group: Group):
    """Compute winner, price, and payoffs (first-price)."""
    import random

    p1, p2 = group.get_players()

    # safety: ensure valuations exist
    for p in (p1, p2):
        if p.valuation is None:
            p.valuation = cu(0)

    b1, b2 = p1.bid, p2.bid

    # nobody bid
    if b1 is None and b2 is None:
        p1.payoff = cu(0)
        p2.payoff = cu(0)
        group.price = cu(0)
        group.winner_id_in_group = 0
        return

    # compare treating None as -1
    c1 = float(b1) if b1 is not None else -1
    c2 = float(b2) if b2 is not None else -1

    if c1 > c2:
        winner, loser = p1, p2
    elif c2 > c1:
        winner, loser = p2, p1
    else:
        winner = random.choice([p1, p2])
        loser = p1 if winner is p2 else p2

    # price rule
    if C.PRICE_RULE == 'first':
        price = winner.bid if winner.bid is not None else cu(0)
    else:
        # optional second-price path if you enable it later
        price = loser.bid if (loser.bid is not None) else cu(0)

    group.price = price
    group.winner_id_in_group = winner.id_in_group

    winner.payoff = max(cu(0), winner.valuation - price)
    loser.payoff = cu(0)
