# experiment1/models.py
from otree.api import *
import random


class C(BaseConstants):
    NAME_IN_URL = 'experiment1'
    PLAYERS_PER_GROUP = 2

    # 6 sessions x 10 rounds
    ROUNDS_PER_SESSION = 10
    NUM_SESSIONS = 6
    NUM_ROUNDS = ROUNDS_PER_SESSION * NUM_SESSIONS


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    price = models.CurrencyField(initial=cu(0))
    winner_id_in_group = models.IntegerField(initial=0)


class Player(BasePlayer):
    valuation = models.CurrencyField(min=0, max=100)
    bid = models.CurrencyField(min=0, max=100, blank=True)
    auto_bid_used = models.BooleanField(initial=False)


# ---------- helpers ----------

def session_and_round(rn: int):
    """Return (session_no 1..6, round_in_session 1..10) for absolute round rn."""
    s = (rn - 1) // C.ROUNDS_PER_SESSION + 1
    r = (rn - 1) % C.ROUNDS_PER_SESSION + 1
    return s, r


def rules_for_round(rn: int):
    """What rules apply in this round?"""
    s, _ = session_and_round(rn)
    price = 'first' if s <= 3 else 'second'
    matching = 'random' if s in (1, 4) else 'fixed'
    chat = s in (3, 6)
    return dict(price=price, matching=matching, chat=chat)


def draw_valuation() -> currency:
    # uniform in cents, 0.00 .. 100.00
    return cu(random.randint(0, 10000)) / 100


# ---------- oTree hooks ----------

def creating_session(subsession: Subsession):
    """Group players & draw valuations each round."""
    s, r = session_and_round(subsession.round_number)
    rules = rules_for_round(subsession.round_number)

    if rules['matching'] == 'random':
        subsession.group_randomly()
    else:
        # fixed partner within each 10-round block
        base_round = (s - 1) * C.ROUNDS_PER_SESSION + 1
        if r == 1:
            subsession.group_randomly()
        else:
            subsession.group_like_round(base_round)

    for p in subsession.get_players():
        p.valuation = draw_valuation()


def set_payoffs(group: Group):
    """Compute price & payoffs after both bids are in, including auto-bid rules."""
    rules = rules_for_round(group.round_number)
    first_price = (rules['price'] == 'first')

    p1, p2 = group.get_players()

    # Fill in automatic bids on any missing submissions
    for p in (p1, p2):
        if p.bid is None:
            p.auto_bid_used = True
            p.bid = (p.valuation / 2) if first_price else p.valuation

    # Determine winner (ties broken randomly)
    if p1.bid > p2.bid:
        winner, loser = p1, p2
    elif p2.bid > p1.bid:
        winner, loser = p2, p1
    else:
        winner = random.choice([p1, p2])
        loser = p1 if winner is p2 else p2

    # Prices by format
    price = loser.bid if not first_price else winner.bid

    # If an automatic bid ends up being the highest, BOTH players get 0 payoff
    # (per your spec for both first-price(v/2) and second-price(v) auto-bids).
    if winner.auto_bid_used:
        group.price = cu(0)
        group.winner_id_in_group = 0
        winner.payoff = cu(0)
        loser.payoff = cu(0)
        return

    # Standard payoffs
    group.price = price
    group.winner_id_in_group = winner.id_in_group
    winner.payoff = max(cu(0), winner.valuation - price)
    loser.payoff = cu(0)


