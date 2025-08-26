# experiment1/models.py
from otree.api import *
from random import randint, choice
import math


class C(BaseConstants):
    NAME_IN_URL = 'experiment1'
    PLAYERS_PER_GROUP = 2

    ROUNDS_PER_SESSION = 10
    NUM_ROUNDS = 6 * ROUNDS_PER_SESSION


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    price = models.CurrencyField(initial=cu(0))
    winner_id_in_group = models.IntegerField()


class Player(BasePlayer):
    valuation = models.CurrencyField()
    bid = models.CurrencyField(min=0, max=100, blank=True)


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
            subsession.group_randomly()
        else:
            subsession.group_like_round(base_round)

    # draw valuations for all players every round
    for p in subsession.get_players():
        p.valuation = random_valuation()


def set_group_payoffs(group: Group):
    p1, p2 = group.get_players()
    b1 = p1.bid if p1.bid is not None else cu(0)
    b2 = p2.bid if p2.bid is not None else cu(0)

    rules = rules_for_round(group.round_number)
    price_rule = rules['price_rule']
    
    # Check for tie bids
    if b1 == b2:
        # Check if the tie is the default bot bid
        if (price_rule == 'first' and b1 == p1.valuation/2 and p2.role == 'bot') or \
           (price_rule == 'second' and b1 == p1.valuation and p2.role == 'bot'):
            p1.payoff = cu(0)
            p2.payoff = cu(0)
            group.price = cu(0)
            group.winner_id_in_group = 0
            return
        
        # Tie-breaking logic as per the document
        winner = choice([p1, p2])
        loser = p1 if winner is p2 else p2

        if price_rule == 'first':
            # Payoff = Your valuation - Your bid^2
            winner.payoff = winner.valuation - (winner.bid ** 2)
            loser.payoff = loser.valuation - (loser.bid ** 2)
            group.price = winner.bid
            group.winner_id_in_group = winner.id_in_group

        else: # Second-price
            # Payoff = Your valuation - Your opponent's bid^2
            winner.payoff = winner.valuation - (loser.bid ** 2)
            loser.payoff = loser.valuation - (winner.bid ** 2)
            group.price = winner.bid # This seems wrong in the instructions, but matches the formula.
            group.winner_id_in_group = winner.id_in_group
            
    else:
        # Normal win/loss
        if b1 > b2:
            winner, loser = p1, p2
        else:
            winner, loser = p2, p1

        if price_rule == 'first':
            price = winner.bid
            winner.payoff = winner.valuation - price
            loser.payoff = cu(0)
        else: # Second-price
            price = loser.bid
            winner.payoff = winner.valuation - price
            loser.payoff = cu(0)
            
        group.price = price
        group.winner_id_in_group = winner.id_in_group

