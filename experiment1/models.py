# experiment1/models.py
from otree.api import *     # brings in Base*, cu, models, etc.

class C(BaseConstants):
    NAME_IN_URL = 'experiment1'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 10
    PRICE_RULE = 'first'     # first-price
    MATCHING   = 'random'    # random matching each round
    TIE_RULE   = 'random'    # random tie-break

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    price = models.CurrencyField(initial=0)
    winner_id_in_group = models.IntegerField(initial=0)

class Player(BasePlayer):
    valuation = models.CurrencyField()
    bid = models.CurrencyField(min=0, max=100, blank=True)
    submitted = models.BooleanField(initial=True)

def creating_session(subsession: Subsession):
    import random
    # match players
    if subsession.round_number == 1:
        subsession.group_randomly()
    else:
        subsession.group_randomly() if C.MATCHING == 'random' else subsession.group_like_round(1)
    # draw valuations
    for p in subsession.get_players():
        p.valuation = cu(round(random.uniform(0, 100), 2))

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


