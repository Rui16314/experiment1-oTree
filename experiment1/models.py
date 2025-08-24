# experiment1/models.py
from otree.api import *
from random import randint, choice


class C(BaseConstants):
    NAME_IN_URL = 'experiment1'
    PLAYERS_PER_GROUP = 2
    # 6 sessions × 10 rounds each
    NUM_ROUNDS = 60


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    price = models.CurrencyField(initial=cu(0))
    winner_id_in_group = models.IntegerField(initial=0)


class Player(BasePlayer):
    # allow null until we set it (pages use field_maybe_none to read safely)
    valuation = models.CurrencyField(blank=True)
    bid = models.CurrencyField(min=0, max=100, blank=True)


# ---------------- helpers used by pages.py ----------------

def phase_and_round_in_session(round_number: int):
    """Return (session_no 1..6, round_in_session 1..10) for a global round number."""
    session_no = (round_number - 1) // 10 + 1
    round_in_session = (round_number - 1) % 10 + 1
    return session_no, round_in_session


def rules_for_round(round_number: int):
    """
    Sessions 1–3: first-price; 4–6: second-price.
    Sessions 1 & 4: random matching; 2 & 5: fixed; 3 & 6: fixed + chat (chat is informational).
    """
    s, _ = phase_and_round_in_session(round_number)
    price = 'first' if s <= 3 else 'second'
    matching = 'random' if s in (1, 4) else 'fixed'
    chat = s in (3, 6)
    return dict(price=price, matching=matching, chat=chat)


def draw_valuation():
    # uniform 0–100 with 2 decimals
    return cu(randint(0, 10000)) / 100


# ---------------- oTree hooks ----------------

def creating_session(subsession: Subsession):
    """
    Group players and draw valuations for every round.
    For fixed sessions, keep the same pairs within the 10-round block.
    """
    session_no, round_in_session = phase_and_round_in_session(subsession.round_number)
    r = rules_for_round(subsession.round_number)

    if r['matching'] == 'random':
        subsession.group_randomly()
    else:
        base_round = (session_no - 1) * 10 + 1
        if round_in_session == 1:
            subsession.group_randomly()          # pick pairs at the start of the session
        else:
            subsession.group_like_round(base_round)

    for p in subsession.get_players():
        # set a fresh valuation each round
        p.valuation = draw_valuation()


def set_payoffs(group: Group):
    """Compute winner, price, and payoffs; ties broken at random."""
    p1, p2 = group.get_players()

    # Treat missing bids as 0 (timeout submission should set this anyway)
    b1 = p1.bid if p1.bid is not None else cu(0)
    b2 = p2.bid if p2.bid is not None else cu(0)

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

