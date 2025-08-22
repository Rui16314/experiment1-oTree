# experiment1/models.py
from otree.api import *
import random


class C(BaseConstants):
    NAME_IN_URL = 'experiment1'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 10


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    # price actually paid by the winner this round
    price = models.CurrencyField(initial=cu(0))
    # 1 or 2 for the winner; 0 means "no winner"
    winner_id_in_group = models.IntegerField(initial=0)


class Player(BasePlayer):
    # private valuation for this round
    valuation = models.CurrencyField()
    # bid for this round (blank before submission)
    bid = models.CurrencyField(min=0, max=100, blank=True)


# ----------------- session and payoff logic -----------------

def _draw_valuation() -> Currency:
    """Uniform 0–100 (two decimals)."""
    return cu(random.randint(0, 10000)) / 100


def creating_session(subsession: Subsession):
    """
    Runs every round. Ensures grouping per matching rule and
    assigns each player's private valuation so it's never None.
    """
    matching = (subsession.session.config.get('matching') or 'random').lower()

    if subsession.round_number == 1:
        # start with a random grouping in round 1
        subsession.group_randomly()
    else:
        if matching == 'fixed':
            # keep the round-1 pairs for all rounds
            subsession.group_like_round(1)
        else:
            subsession.group_randomly()

    # assign valuations in EVERY round
    for p in subsession.get_players():
        p.valuation = _draw_valuation()


def _tiebreak(players, rule: str):
    """Return a single player from a tie, according to rule."""
    rule = (rule or 'random').lower()
    if rule == 'low_id':
        return min(players, key=lambda pp: pp.id_in_group)
    if rule == 'high_id':
        return max(players, key=lambda pp: pp.id_in_group)
    # default random
    return random.choice(players)


def set_payoffs(group: Group):
    """Compute winner, price and payoffs for a 2-player auction."""
    p1, p2 = group.get_players()

    # protect against unexpected None bids (timeouts etc.)
    for p in (p1, p2):
        if p.bid is None:
            p.bid = cu(0)

    # decide winner
    if p1.bid > p2.bid:
        winner, loser = p1, p2
    elif p2.bid > p1.bid:
        winner, loser = p2, p1
    else:
        # tie: use session-configured rule (default random)
        tie_rule = (group.session.config.get('tie_rule') or 'random')
        winner = _tiebreak([p1, p2], tie_rule)
        loser = p1 if winner is p2 else p2

    # price rule: first (default) or second
    price_rule = (group.session.config.get('price_rule') or 'first').lower()
    if price_rule == 'second':
        price = loser.bid
    else:
        price = winner.bid

    group.price = price
    group.winner_id_in_group = winner.id_in_group if winner else 0

    # payoffs: win -> valuation - price ; lose -> 0
    winner.payoff = winner.valuation - price
    loser.payoff = cu(0)
