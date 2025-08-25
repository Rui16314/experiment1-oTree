# experiment1/models.py
from otree.api import *
from random import randint, choice


class C(BaseConstants):
    NAME_IN_URL = 'experiment1'
    PLAYERS_PER_GROUP = 2

    # 6 sessions × 10 rounds each
    ROUNDS_PER_SESSION = 10
    NUM_SESSIONS = 6
    NUM_ROUNDS = ROUNDS_PER_SESSION * NUM_SESSIONS


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    price = models.CurrencyField(initial=cu(0))
    winner_id_in_group = models.IntegerField(initial=0)


class Player(BasePlayer):
    valuation = models.CurrencyField()
    bid = models.CurrencyField(min=0, max=100, blank=True)


# ---------- helpers ----------
def phase_and_round_in_session(round_number: int):
    """(session_no 1..6, round_in_session 1..10)"""
    s = (round_number - 1) // C.ROUNDS_PER_SESSION + 1
    r = (round_number - 1) % C.ROUNDS_PER_SESSION + 1
    return s, r


def rules_for_round(round_number: int):
    """Return dict(price='first'|'second', matching='random'|'fixed', chat: bool)."""
    session_no, _ = phase_and_round_in_session(round_number)
    price = 'first' if session_no <= 3 else 'second'
    matching = 'random' if session_no in (1, 4) else 'fixed'
    chat = session_no in (3, 6)
    return dict(price=price, matching=matching, chat=chat)


def _draw_valuation() -> currency:
    # uniform 0–100 cents
    return cu(randint(0, 10000)) / 100


# ---------- oTree hooks ----------
def creating_session(subsession: Subsession):
    """Set groups and give every player a valuation BEFORE any page renders."""
    rules = rules_for_round(subsession.round_number)
    session_no, round_in_session = phase_and_round_in_session(subsession.round_number)

    if rules['matching'] == 'random':
        subsession.group_randomly()
    else:
        base_round = (session_no - 1) * C.ROUNDS_PER_SESSION + 1
        if round_in_session == 1:
            subsession.group_randomly()
        else:
            subsession.group_like_round(base_round)

    # give everyone a valuation now so templates can read it safely
    for p in subsession.get_players():
        p.valuation = _draw_valuation()


def set_payoffs(group: Group):
    p1, p2 = group.get_players()
    b1 = p1.bid or cu(0)
    b2 = p2.bid or cu(0)

    if b1 > b2:
        winner, loser = p1, p2
    elif b2 > b1:
        winner, loser = p2, p1
    else:
        winner = choice([p1, p2])
        loser = p1 if winner is p2 else p2

    price_rule = rules_for_round(group.round_number)['price']
    price = loser.bid if price_rule == 'second' else winner.bid

    group.price = price
    group.winner_id_in_group = winner.id_in_group
    winner.payoff = max(cu(0), winner.valuation - price)
    loser.payoff = cu(0)



