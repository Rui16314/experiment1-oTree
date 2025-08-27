# experiment1/models.py
from otree.api import *
from random import choice, randint
import json


class C(BaseConstants):
    NAME_IN_URL = 'experiment1'
    PLAYERS_PER_GROUP = 2
    ROUNDS_PER_SESSION = 10
    NUM_SESSIONS = 6
    NUM_ROUNDS = ROUNDS_PER_SESSION * NUM_SESSIONS


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    # price actually paid this round
    price = models.CurrencyField(initial=cu(0))
    # winner id_in_group (1 or 2), 0 if no winner
    winner_id_in_group = models.IntegerField(initial=0)

    # store chat history for the round (JSON text)
    chat_history = models.LongStringField(initial='[]')


class Player(BasePlayer):
    # private valuation for the round
    valuation = models.CurrencyField()
    # user-entered bid (optional)
    bid = models.CurrencyField(min=0, max=100, blank=True)


# ---------- helpers about session/round and rules ----------

def phase_and_round_in_session(rn: int):
    """returns (session_no 1..6, round_in_session 1..10)"""
    session_no = (rn - 1) // C.ROUNDS_PER_SESSION + 1
    round_in_session = (rn - 1) % C.ROUNDS_PER_SESSION + 1
    return session_no, round_in_session


def rules_for_round(rn: int):
    """Rules by session:
       S1..S3: first-price (S3 has chat)
       S4..S6: second-price (S6 has chat)
       Matching: random in S1, S4; fixed within-session in others
    """
    s, _ = phase_and_round_in_session(rn)
    price = 'first' if s <= 3 else 'second'
    matching = 'random' if s in (1, 4) else 'fixed'
    chat = s in (3, 6)
    return dict(price=price, matching=matching, chat=chat)


def draw_valuation():
    # uniform 0–100 (two decimals)
    return cu(randint(0, 10000)) / 100


# ---------- oTree hooks ----------

def creating_session(subsession: Subsession):
    """Group players & draw valuations each round."""
    s, ris = phase_and_round_in_session(subsession.round_number)
    r = rules_for_round(subsession.round_number)

    if r['matching'] == 'random':
        subsession.group_randomly()
    else:
        # fixed partner within the 10-round session block
        base_round = (s - 1) * C.ROUNDS_PER_SESSION + 1
        if ris == 1:
            subsession.group_randomly()          # choose pairs at start of session
        else:
            subsession.group_like_round(base_round)

    for p in subsession.get_players():
        p.valuation = draw_valuation()


def _effective_bid(p: Player):
    """
    Return (bid_value, was_auto) where:
    - if the player did not submit a bid, we take valuation/2 automatically;
    - was_auto indicates whether this was such an automatic bid.
    """
    if p.bid is None:
        return p.valuation / 2, True
    return p.bid, False


def set_payoffs(group: Group):
    """Compute price & payoffs after both bids are in.
       Special rule: if the winning bid was an automatic (valuation/2) bid,
       then *both* players earn 0 this round.
    """
    p1, p2 = group.get_players()

    b1, auto1 = _effective_bid(p1)
    b2, auto2 = _effective_bid(p2)

    # winner/loser (break ties at random)
    if b1 > b2:
        winner, loser, winner_auto = p1, p2, auto1
    elif b2 > b1:
        winner, loser, winner_auto = p2, p1, auto2
    else:
        # tie -> pick randomly
        winner = choice([p1, p2])
        loser = p1 if winner is p2 else p2
        # if tie, neither is "winning because automatic"
        # (rule below only triggers when the *winning* bid is automatic)
        winner_auto = (auto1 if winner is p1 else auto2)

    r = rules_for_round(group.round_number)

    # If winning bid was automatic (valuation/2), both get zero.
    if winner_auto:
        group.price = cu(0)
        group.winner_id_in_group = 0
        p1.payoff = cu(0)
        p2.payoff = cu(0)
        return

    # otherwise usual pricing
    if r['price'] == 'first':
        price_paid = winner.bid if winner.bid is not None else winner.valuation / 2
    else:  # second-price
        price_paid = (loser.bid if loser.bid is not None else loser.valuation / 2)

    group.price = price_paid
    group.winner_id_in_group = winner.id_in_group

    winner.payoff = max(cu(0), winner.valuation - price_paid)
    loser.payoff = cu(0)
