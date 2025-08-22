# experiment1/models.py
from otree.api import *
from random import randint

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
    valuation = models.CurrencyField()
    bid = models.CurrencyField(min=0, max=100, blank=True)

def draw_valuation():
    return cu(randint(0, 10000)) / 100  # 0–100 with cents

def creating_session(subsession: Subsession):
    # group randomly each round (or copy round 1 if you want fixed)
    subsession.group_randomly()
    for p in subsession.get_players():
        p.valuation = draw_valuation()

def set_payoffs(group: Group):
    p1, p2 = group.get_players()
    b1 = p1.bid or cu(0)
    b2 = p2.bid or cu(0)
    if b1 > b2:
        winner, loser = p1, p2
        group.price = b1
    elif b2 > b1:
        winner, loser = p2, p1
        group.price = b2
    else:
        winner = loser = None
        group.price = cu(0)

    group.winner_id_in_group = winner.id_in_group if winner else 0
    for p in (p1, p2):
        p.payoff = (p.valuation - group.price) if p is winner else cu(0)

