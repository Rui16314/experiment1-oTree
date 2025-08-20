from otree.api import *

class C(BaseConstants):
    NAME_IN_URL = 'experiment1'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 10
    PRICE_RULE = 'first'      # first or second
    MATCHING   = 'random'     # random or fixed
    TIE_RULE   = 'random'     # random or split
    CHAT       = False        # no chat in Experiment 1
    BIN_SIZE   = 10           # for the summary plot

class Subsession(BaseSubsession): pass

class Group(BaseGroup):
    price = CurrencyField(initial=0)
    winner_id_in_group = IntegerField(initial=0)

class Player(BasePlayer):
    valuation = CurrencyField()
    bid = CurrencyField(min=0, max=100, blank=True)
    submitted = BooleanField(initial=True)

def creating_session(subsession: Subsession):
    import random
    # matching
    if subsession.round_number == 1:
        subsession.group_randomly()
    else:
        if C.MATCHING == 'fixed':
            subsession.group_like_round(1)
        else:
            subsession.group_randomly()
    # valuations
    for p in subsession.get_players():
        p.valuation = cu(round(random.uniform(0, 100), 2))

def set_payoffs(group: Group):
    import random
    p1, p2 = group.get_players()
    b1, b2 = p1.bid, p2.bid
    c1 = float(b1) if b1 is not None else -1.0
    c2 = float(b2) if b2 is not None else -1.0

    if b1 is None and b2 is None:
        p1.payoff = cu(0); p2.payoff = cu(0)
        group.price = cu(0); group.winner_id_in_group = 0
        return

    if c1 > c2:
        winner, loser = p1, p2
    elif c2 > c1:
        winner, loser = p2, p1
    else:
        # tie: random winner in Experiment 1
        winner = random.choice([p1, p2])
        loser  = p1 if winner is p2 else p2

    # price
    if C.PRICE_RULE == 'first':
        price = winner.bid if winner.bid is not None else cu(0)
    else:
        price = (loser.bid if loser.bid is not None else cu(0))

    group.price = price
    group.winner_id_in_group = winner.id_in_group
    winner.payoff = max(cu(0), winner.valuation - price)
    loser.payoff = cu(0)
