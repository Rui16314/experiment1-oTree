# experiment1/models.py
from otree.api import (
    BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as cu, CurrencyField, IntegerField, BooleanField,
)


class C(BaseConstants):
    NAME_IN_URL = 'experiment1'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 10

    # treatment knobs (can also be passed via session config)
    PRICE_RULE = 'first'      # 'first' or 'second' (we use 'first' here)
    MATCHING = 'random'       # 'random' or 'fixed' (fixed = like round 1)
    TIE_RULE = 'random'       # what to do on equal bids


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    # clearing results recorded at the group level
    price = CurrencyField(initial=0)
    winner_id_in_group = IntegerField(initial=0)


class Player(BasePlayer):
    # set each round in creating_session; allow blank so None won't crash
    valuation = CurrencyField(blank=True)
    # bid is optional (participant may time out)
    bid = CurrencyField(min=0, max=100, blank=True)
    submitted = BooleanField(initial=False)


# ---- session/round setup -----------------------------------------------------

def creating_session(subsession: Subsession):
    """
    Runs at the start of every round.
    - Do grouping (random each round unless MATCHING='fixed').
    - Draw a fresh private valuation in [0, 100] for each player.
    """
    import random

    if subsession.round_number == 1:
        subsession.group_randomly()
    else:
        if C.MATCHING == 'random':
            subsession.group_randomly()
        else:
            subsession.group_like_round(1)

    # draw valuations (every round)
    for p in subsession.get_players():
        p.valuation = cu(round(random.uniform(0, 100), 2))


# ---- outcome computation -----------------------------------------------------

def set_payoffs(group: Group):
    """
    Called from the results WaitPage after both players advance.
    Computes winner, price (first-price), and payoffs.
    Defensive against missing bids or valuations.
    """
    import random

    p1, p2 = group.get_players()

    # Ensure valuations exist to avoid None subtraction errors.
    # (Should be set in creating_session, but guard just in case.)
    for p in (p1, p2):
        if p.valuation is None:
            p.valuation = cu(0)

    b1, b2 = p1.bid, p2.bid

    # If nobody bid, nothing happens in this round.
    if b1 is None and b2 is None:
        p1.payoff = cu(0)
        p2.payoff = cu(0)
        group.price = cu(0)
        group.winner_id_in_group = 0
        return

    # For comparing who wins, treat None as -1 so any real bid beats it.
    c1 = float(b1) if b1 is not None else -1
    c2 = float(b2) if b2 is not None else -1

    if c1 > c2:
        winner, loser = p1, p2
    elif c2 > c1:
        winner, loser = p2, p1
    else:
        # tie rule (random)
        winner = random.choice([p1, p2])
        loser = p1 if winner is p2 else p2

    # First-price auction: price is the winner's bid
    if C.PRICE_RULE == 'first':
        price = winner.bid if winner.bid is not None else cu(0)
    else:
        # (Optional second-price branch if you enable it later)
        # price = loser.bid if loser.bid is not None else cu(0)
        price = winner.bid if winner.bid is not None else cu(0)

    group.price = price
    group.winner_id_in_group = winner.id_in_group

    winner.payoff = max(cu(0), winner.valuation - price)
    loser.payoff = cu(0)
