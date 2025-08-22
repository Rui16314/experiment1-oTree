# experiment1/models.py
from otree.api import *
from random import randint, choice

class C(BaseConstants):
    NAME_IN_URL = 'experiment1'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 10

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    price = models.CurrencyField(initial=cu(0))
    winner_id_in_group = models.IntegerField(initial=0)

class Player(BasePlayer):
    # allow None while the round is being created, then we set it
    valuation = models.CurrencyField(blank=True)
    bid = models.CurrencyField(min=0, blank=True)

def draw_valuation():
    # uniform 0–100 (cents) with 2 decimals
    return cu(randint(0, 10000)) / 100

def creating_session(subsession: Subsession):
    """Runs at the start of each round. Assign a valuation to every player."""
    for p in subsession.get_players():
        p.valuation = draw_valuation()

def set_payoffs(group: Group):
    p1, p2 = group.get_players()
    b1 = p1.bid or cu(0)
    b2 = p2.bid or cu(0)

    if b1 == b2:
        winner = choice([p1, p2]) if b1 > 0 else None
        loser  = p1 if winner is p2 else p2 if winner else None
    elif b1 > b2:
        winner, loser = p1, p2
    else:
        winner, loser = p2, p1

    if not winner:  # nobody bid
        group.price = cu(0)
        group.winner_id_in_group = 0
        p1.payoff = p2.payoff = cu(0)
        return

    price = winner.bid  # first-price; change here if you later switch rules
    group.price = price
    group.winner_id_in_group = winner.id_in_group

    winner.payoff = max(cu(0), winner.valuation - price)
    loser.payoff = cu(0)

