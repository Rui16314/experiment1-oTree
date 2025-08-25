# experiment1/models.py
from otree.api import *
from random import choice


class C(BaseConstants):
    NAME_IN_URL = 'experiment1'
    PLAYERS_PER_GROUP = 2

    # 6 sessions, 10 rounds each
    SESSIONS = 6
    ROUNDS_PER_SESSION = 10
    NUM_ROUNDS = SESSIONS * ROUNDS_PER_SESSION

    # convenience mapping: session 1..6 -> (price_rule, matching, chat)
    # sessions 1–3: first-price; 4–6: second-price
    # sessions 2 & 5: fixed partners; 3 & 6: with chat
    SESSION_RULES = {
        1: dict(price='first',  matching='random', chat=False),
        2: dict(price='first',  matching='fixed',  chat=False),
        3: dict(price='first',  matching='fixed',  chat=True),
        4: dict(price='second', matching='random', chat=False),
        5: dict(price='second', matching='fixed',  chat=False),
        6: dict(price='second', matching='fixed',  chat=True),
    }


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    price = models.CurrencyField(initial=cu(0))
    winner_id_in_group = models.IntegerField(initial=0)


class Player(BasePlayer):
    valuation = models.CurrencyField()
    bid = models.CurrencyField(min=0, max=100, blank=True)
    timed_out = models.BooleanField(initial=False)  # True if system set v/2


# ---------- helpers ----------

def session_no_and_round_in_session(round_number: int):
    """Return (session_no: 1..6, round_in_session: 1..10)."""
    s_no = (round_number - 1) // C.ROUNDS_PER_SESSION + 1
    r_in = (round_number - 1) % C.ROUNDS_PER_SESSION + 1
    return s_no, r_in


def rules_for_round(round_number: int):
    s_no, _ = session_no_and_round_in_session(round_number)
    return C.SESSION_RULES[s_no]


def draw_valuation() -> currency:
    # uniform 0–100 in cents (two decimals)
    # (this matches the “0..100 in cents” rule in your doc)
    return cu(self_random.randint(0, 10000)) / 100


# ---------- oTree hooks ----------

def creating_session(subsession: Subsession):
    """Group players & draw valuations each round according to session rules."""
    s_no, r_in = session_no_and_round_in_session(subsession.round_number)
    r = rules_for_round(subsession.round_number)

    if r['matching'] == 'random':
        subsession.group_randomly()
    else:
        # fixed partner within each 10-round session block
        base_round = (s_no - 1) * C.ROUNDS_PER_SESSION + 1
        if r_in == 1:
            subsession.group_randomly()          # choose pairs at start of session
        else:
            subsession.group_like_round(base_round)

    for p in subsession.get_players():
        # fresh valuation every round
        p.valuation = cu(self_random.randint(0, 10000)) / 100


def set_payoffs(group: Group):
    """Implements first/second price, ties random, and the v/2 timeout rule."""
    p1, p2 = group.get_players()

    # bids may still be None if a participant closed the tab mid-request
    b1 = p1.bid if p1.bid is not None else cu(0)
    b2 = p2.bid if p2.bid is not None else cu(0)

    # winner/loser by higher bid (ties: random)
    if b1 > b2:
        winner, loser = p1, p2
    elif b2 > b1:
        winner, loser = p2, p1
    else:
        winner = choice([p1, p2])
        loser = p1 if winner is p2 else p2

    price_rule = rules_for_round(group.round_number)['price']
    price = loser.bid if price_rule == 'second' else winner.bid

    # If the winner was auto-bid v/2 (timed out), BOTH payoffs are 0 (your rule).
    if winner.timed_out:
        group.price = cu(0)
        group.winner_id_in_group = 0
        p1.payoff = cu(0)
        p2.payoff = cu(0)
        return

    group.price = price
    group.winner_id_in_group = winner.id_in_group

    # Payoffs: winner gets valuation − price; loser gets 0
    winner.payoff = max(cu(0), winner.valuation - price)
    (loser).payoff = cu(0)


# small RNG helper tied to session to avoid import-side effects
class self_random:
    import random as _r
    _rng = _r.Random()

    @classmethod
    def randint(cls, a, b):
        return cls._rng.randint(a, b)



