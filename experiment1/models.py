# experiment1/models.py
from otree.api import BaseConstants, BaseSubsession, BaseGroup, BasePlayer, cu, models
from random import randint, choice

class C(BaseConstants):
    NAME_IN_URL = 'experiment1'
    PLAYERS_PER_GROUP = 2
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



# -------------------- helpers about sessions/rules --------------------

def session_no_and_round_in_session(round_number: int):
    """
    Return (session_no, round_in_session), both 1-indexed.
    Session 1 = rounds 1..10, session 2 = 11..20, ..., session 6 = 51..60.
    """
    s = (round_number - 1) // C.ROUNDS_PER_SESSION + 1
    r = (round_number - 1) % C.ROUNDS_PER_SESSION + 1
    return s, r


def rules_for_round(round_number: int):
    """
    What rules apply in this (global) round?
    - price: 'first' or 'second'
    - matching: 'random' or 'fixed'
    - chat: True/False (enabled)
    """
    s, _ = session_no_and_round_in_session(round_number)
    price = 'first' if s <= 3 else 'second'
    matching = 'random' if s in (1, 4) else 'fixed'
    chat = s in (3, 6)
    return dict(price=price, matching=matching, chat=chat)
def _draw_valuation():
    """
    Uniform 0..100, two decimals.
    (randint gives an int in cents; divide by 100.)
    """
    return cu(randint(0, 10000) / 100)


# -------------------- oTree hooks --------------------

def creating_session(subsession: Subsession):
    """
    - Set matching according to the session's rule.
    - Draw valuations for each player in the round.
    """
    s_no, r_in_s = session_no_and_round_in_session(subsession.round_number)
    r = rules_for_round(subsession.round_number)

    if r['matching'] == 'random':
        # new random pairs each round
        subsession.group_randomly()
    else:
        # fixed partner within the 10-round block
        first_round_of_block = (s_no - 1) * C.ROUNDS_PER_SESSION + 1
        if r_in_s == 1:
            subsession.group_randomly()  # pick pairings at start of the block
        else:
            subsession.group_like_round(first_round_of_block)

    # draw valuations
    for p in subsession.get_players():
        p.valuation = _draw_valuation()


def set_group_payoffs(group: Group):
    """
    Compute winner, price, and payoffs.
    - If a player did not submit a bid (None), treat it as 0.
    - Ties are broken at random.
    - First-price: price = winner's bid
      Second-price: price = loser's bid
    """
    p1, p2 = group.get_players()

    b1 = p1.bid if p1.bid is not None else cu(0)
    b2 = p2.bid if p2.bid is not None else cu(0)

    # Determine winner (break ties randomly)
    if b1 > b2:
        winner, loser = p1, p2
    elif b2 > b1:
        winner, loser = p2, p1
    else:
        winner = choice([p1, p2])
        loser = p1 if winner is p2 else p2

    rule = rules_for_round(group.round_number)
    price = winner.bid if rule['price'] == 'first' else loser.bid

    group.price = price
    group.winner_id_in_group = winner.id_in_group

    # Payoffs
    winner.payoff = max(cu(0), winner.valuation - price)
    loser.payoff = cu(0)


# Some codebases call this function 'set_payoffs'; provide an alias for safety.
set_payoffs = set_group_payoffs
