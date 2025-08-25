from otree.api import *
from random import randint, choice
import time

class C(BaseConstants):
    NAME_IN_URL = 'experiment1'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 60
    ROUNDS_PER_SESSION = 10  # exactly 10 per session block


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    price = models.CurrencyField(initial=cu(0))
    winner_id_in_group = models.IntegerField(initial=0)


class Player(BasePlayer):
    # currency values in [0, 100] with cents allowed
    valuation = models.CurrencyField()
    bid = models.CurrencyField(min=0, max=100, blank=True)


# ---------- helpers: session/round & rules ----------

def phase_and_round_in_session(rn: int):
    """returns (session_no 1..6, round_in_session 1..10)"""
    s = (rn - 1) // C.ROUNDS_PER_SESSION + 1
    ris = (rn - 1) % C.ROUNDS_PER_SESSION + 1
    return s, ris


def rules_for_round(rn: int):
    """returns dict(price='first'|'second', matching='random'|'fixed', chat=bool)"""
    s, _ = phase_and_round_in_session(rn)
    price = 'first' if s <= 3 else 'second'
    matching = 'random' if s in (1, 4) else 'fixed'
    chat = s in (3, 6)
    return dict(price=price, matching=matching, chat=chat)


def draw_valuation() -> currency:
    # uniform over 0..100 with 2 decimals
    return cu(randint(0, 10000)) / 100


# ---------- oTree hooks ----------

def creating_session(subsession: Subsession):
    """Group players & draw valuations each round."""
    s, round_in_s = phase_and_round_in_session(subsession.round_number)
    r = rules_for_round(subsession.round_number)

    if r['matching'] == 'random':
        subsession.group_randomly()
    else:
        # fixed partner within the 10-round session block
        base_round = (s - 1) * C.ROUNDS_PER_SESSION + 1
        if round_in_s == 1:
            subsession.group_randomly()  # choose pairs at start of session
        else:
            subsession.group_like_round(base_round)

    # give everyone a valuation (so templates never see null)
    for p in subsession.get_players():
        p.valuation = draw_valuation()


def set_payoffs(group: Group):
    """
    Compute price & payoffs after both bids are in.

    If a player does not submit a bid (timeout), that player loses and receives 0.
    If both fail to bid, both receive 0 and price=0.
    """
    p1, p2 = group.get_players()
    b1 = p1.bid
    b2 = p2.bid

    # both missed -> both 0
    if b1 is None and b2 is None:
        group.price = cu(0)
        group.winner_id_in_group = 0
        p1.payoff = cu(0)
        p2.payoff = cu(0)
        return

    # decide winner/loser, honoring "no-bid loses"
    if b1 is None and b2 is not None:
        winner, loser = p2, p1
    elif b2 is None and b1 is not None:
        winner, loser = p1, p2
    else:
        # both have bids -> usual comparison with random tiebreak
        if b1 > b2:
            winner, loser = p1, p2
        elif b2 > b1:
            winner, loser = p2, p1
        else:
            winner = choice([p1, p2])
            loser = p1 if winner is p2 else p2

    price_rule = rules_for_round(group.round_number)['price']
    if price_rule == 'first':
        price = winner.bid if winner.bid is not None else cu(0)
    else:
        price = loser.bid if loser.bid is not None else cu(0)

    group.price = price
    group.winner_id_in_group = winner.id_in_group

    # payoffs
    winner.payoff = max(cu(0), winner.valuation - price)
    loser.payoff = cu(0)

class ChatMessage(ExtraModel):  # ADD
    group = models.Link(Group)
    sender_id_in_group = models.IntegerField()
    text = models.LongStringField()
    ts = models.FloatField()  # epoch seconds


def chat_history_for(group):  # ADD
    rows = ChatMessage.filter(group=group).order_by('id')
    return [{'sid': r.sender_id_in_group, 'text': r.text, 'ts': r.ts} for r in rows]



