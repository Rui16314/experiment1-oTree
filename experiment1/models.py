# experiment1/models.py
from otree.api import *
from random import randint, choice


class C(BaseConstants):
    NAME_IN_URL = 'experiment1'
    PLAYERS_PER_GROUP = 2

    ROUNDS_PER_SESSION = 10
    NUM_ROUNDS = 6 * ROUNDS_PER_SESSION  # 6 sessions total


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    price = models.CurrencyField(initial=cu(0))
    winner_id_in_group = models.IntegerField()


class Player(BasePlayer):
    valuation = models.CurrencyField()                       # 0–100
    bid = models.CurrencyField(min=0, max=100, blank=True)   # may be blank if timeout


# ----------------- helpers -----------------

def session_no_and_round_in_session(round_number: int):
    """Return (session_no 1..6, round_in_session 1..10)."""
    s = (round_number - 1) // C.ROUNDS_PER_SESSION + 1
    r = (round_number - 1) % C.ROUNDS_PER_SESSION + 1
    return s, r


def rules_for_round(round_number: int):
    """
    Returns a dict with:
      price_rule: 'first' | 'second'
      matching:   'random' | 'fixed'
      chat:       bool
    Sessions:
      1: first / random / no chat
      2: first / fixed  / no chat
      3: first / fixed  / chat
      4: second / random / no chat
      5: second / fixed  / no chat
      6: second / fixed  / chat
    """
    s, _ = session_no_and_round_in_session(round_number)
    price = 'first' if s <= 3 else 'second'
    matching = 'random' if s in (1, 4) else 'fixed'
    chat = s in (3, 6)
    return dict(price_rule=price, matching=matching, chat=chat)


def random_valuation():
    # uniform 0–100 with 2 decimals
    return cu(randint(0, 10000)) / 100


# ----------------- oTree hooks -----------------

def creating_session(subsession: Subsession):
    """Group players and draw valuations each round."""
    rules = rules_for_round(subsession.round_number)
    s, r_in_s = session_no_and_round_in_session(subsession.round_number)

    if rules['matching'] == 'random':
        subsession.group_randomly()
    else:
        # fixed opponents within each 10-round block
        base_round = (s - 1) * C.ROUNDS_PER_SESSION + 1
        if r_in_s == 1:
            subsession.group_randomly()  # choose pairs at the start of the block
        else:
            subsession.group_like_round(base_round)

    # draw valuations for all players every round
    for p in subsession.get_players():
        p.valuation = random_valuation()


# do the payoff computation on Group so we can call it from a WaitPage
def set_group_payoffs(group: Group):
    p1, p2 = group.get_players()

    # in case of timeouts / no entry, treat missing bids as 0
    b1 = p1.bid if p1.bid is not None else cu(0)
    b2 = p2.bid if p2.bid is not None else cu(0)

    # winner/loser (ties broken randomly)
    if b1 > b2:
        winner, loser = p1, p2
    elif b2 > b1:
        winner, loser = p2, p1
    else:
        winner = choice([p1, p2])
        loser = p1 if winner is p2 else p2

    # first-price vs second-price
    price_rule = rules_for_round(group.round_number)['price_rule']
    price = winner.bid if price_rule == 'first' else loser.bid

    group.price = price
    group.winner_id_in_group = winner.id_in_group

    # payoffs
    winner.payoff = max(cu(0), winner.valuation - price)
    loser.payoff = cu(0)



