# experiment1/models.py
from otree.api import *
import random


class C(BaseConstants):
    NAME_IN_URL = 'experiment1'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 60
    ROUNDS_PER_SESSION = 10


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    price = models.CurrencyField(initial=cu(0))
    winner_id_in_group = models.IntegerField(initial=0)


class Player(BasePlayer):
    valuation = models.CurrencyField()
    bid = models.CurrencyField(min=0, max=100, blank=True)


# ---------- helpers ----------

def session_round_info(round_number: int):
    """Return (session_no 1..6, round_in_session 1..10)."""
    s_no = (round_number - 1) // C.ROUNDS_PER_SESSION + 1
    r_in_s = (round_number - 1) % C.ROUNDS_PER_SESSION + 1
    return s_no, r_in_s


def rules_for_round(round_number: int):
    """Rules that apply in this round."""
    s_no, _ = session_round_info(round_number)
    price = 'first' if s_no <= 3 else 'second'
    matching = 'random' if s_no in (1, 4) else 'fixed'
    chat = s_no in (3, 6)
    return dict(price=price, matching=matching, chat=chat)


def draw_valuation() -> currency:
    # Uniform 0–100 (two decimals)
    return cu(random.randint(0, 10000)) / 100


# ---------- oTree hooks ----------

def creating_session(subsession: Subsession):
    """Group players and assign private valuations each round."""
    s_no, r_in_s = session_round_info(subsession.round_number)
    r = rules_for_round(subsession.round_number)

    if r['matching'] == 'random':
        subsession.group_randomly()
    else:
        base_round = (s_no - 1) * C.ROUNDS_PER_SESSION + 1
        if r_in_s == 1:
            subsession.group_randomly()           # choose pairs at the start
        else:
            subsession.group_like_round(base_round)

    for p in subsession.get_players():
        p.valuation = draw_valuation()


def set_payoffs(group: Group):
    """Compute price & payoffs after both bids are in."""
    p1, p2 = group.get_players()
    b1 = p1.bid or cu(0)
    b2 = p2.bid or cu(0)

    # winner (break ties at random)
    if b1 > b2:
        winner, loser = p1, p2
    elif b2 > b1:
        winner, loser = p2, p1
    else:
        winner = random.choice([p1, p2])
        loser = p1 if winner is p2 else p2

    price_rule = rules_for_round(group.round_number)['price']
    price = (loser.bid if price_rule == 'second' else winner.bid) or cu(0)

    group.price = price
    group.winner_id_in_group = winner.id_in_group

    # payoff = value - price if you win; else 0
    winner.payoff = max(cu(0), (winner.valuation or cu(0)) - price)
    loser.payoff = cu(0)


