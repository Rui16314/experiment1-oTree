# experiment1/models.py
from otree.api import BaseConstants, BaseSubsession, BaseGroup, BasePlayer
from otree.api import Currency as cu, models


class C(BaseConstants):
    NAME_IN_URL = 'experiment1'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 10

    # configurable rules (used by pages/templates)
    PRICE_RULE = 'first'     # 'first' or 'second'
    MATCHING = 'random'      # 'random' or 'fixed'
    TIE_RULE = 'random'      # 'random' or 'split' (only for second-price if you want)


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    price = models.CurrencyField(initial=0)
    winner_id_in_group = models.IntegerField(initial=0)


class Player(BasePlayer):
    valuation = models.CurrencyField()
    bid = models.CurrencyField(min=0, max=100, blank=True)
    submitted = models.BooleanField(initial=True)


# ----- session helpers -----

def creating_session(subsession: Subsession):
    """Assign groups + private valuations each round."""
    import random

    # grouping
    if subsession.round_number == 1:
        if C.MATCHING.lower() == 'fixed':
            # fixed partner for all rounds
            subsession.group_randomly()  # once in round 1, then copy below
        else:
            subsession.group_randomly()
    else:
        if C.MATCHING.lower() == 'fixed':
            subsession.group_like_round(1)
        else:
            subsession.group_randomly()

    # assign valuations in every round
    for p in subsession.get_players():
        # uniform 0–100 with 2 decimals
        p.valuation = cu(round(random.uniform(0, 100), 2))


def set_payoffs(group: Group):
    """Compute price & payoffs after both bids are in."""
    import random
    p1, p2 = group.get_players()
    b1, b2 = p1.bid, p2.bid

    # Treat missing bids as 0 (should not happen if you used timeout_submission)
    b1 = cu(0) if b1 is None else b1
    b2 = cu(0) if b2 is None else b2

    # nobody bid
    if b1 == 0 and b2 == 0:
        p1.payoff = cu(0)
        p2.payoff = cu(0)
        group.price = cu(0)
        group.winner_id_in_group = 0
        return

    # determine winner (ties by rule)
    if b1 > b2:
        winner, loser = p1, p2
    elif b2 > b1:
        winner, loser = p2, p1
    else:
        # tie: random winner
        winner = random.choice([p1, p2])
        loser = p1 if winner is p2 else p2

    # price rule
    if C.PRICE_RULE.lower() == 'second':
        price = loser.bid
    else:  # 'first'
        price = winner.bid

    group.price = price
    group.winner_id_in_group = winner.id_in_group

    # payoffs (value - price if you win, 0 otherwise)
    winner.payoff = max(cu(0), winner.valuation - price)
    loser.payoff = cu(0)

