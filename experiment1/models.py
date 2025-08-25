# experiment1/models.py
from otree.api import *
from random import randint, choice

class C(BaseConstants):
    NAME_IN_URL = 'experiment1'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 60

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    price = models.CurrencyField(initial=cu(0))
    winner_id_in_group = models.IntegerField(initial=0)

class Player(BasePlayer):
    valuation = models.CurrencyField()
    bid = models.CurrencyField(min=0, max=100, blank=True)

# ---- helpers you already have (or equivalent) ----
def draw_valuation():
    # uniform 0–100 with cents
    return cu(randint(0, 10000)) / 100

def phase_and_round_in_session(rn: int):
    return (rn - 1) // 10 + 1, (rn - 1) % 10 + 1

def rules_for_round(rn: int):
    s, _ = phase_and_round_in_session(rn)
    return dict(price=('first' if s <= 3 else 'second'),
                matching=('random' if s in (1, 4) else 'fixed'),
                chat=(s in (3, 6)))

def creating_session(subsession: Subsession):
    # your grouping (random vs fixed within 10-round blocks)
    s, ris = phase_and_round_in_session(subsession.round_number)
    if rules_for_round(subsession.round_number)['matching'] == 'fixed':
        base = (s - 1) * 10 + 1
        subsession.group_randomly() if ris == 1 else subsession.group_like_round(base)
    else:
        subsession.group_randomly()

    # *** set valuation for EVERY player, EVERY round ***
    for p in subsession.get_players():
        p.valuation = draw_valuation()

def set_payoffs(group: Group):
    p1, p2 = group.get_players()

    # --- last-resort guard (prevents None ever reaching templates) ---
    if p1.field_maybe_none('valuation') is None:
        p1.valuation = draw_valuation()
    if p2.field_maybe_none('valuation') is None:
        p2.valuation = draw_valuation()
    # -----------------------------------------------------------------

    b1 = p1.bid or cu(0)
    b2 = p2.bid or cu(0)

    if b1 > b2:
        winner, loser = p1, p2
    elif b2 > b1:
        winner, loser = p2, p1
    else:
        winner = choice([p1, p2]); loser = p1 if winner is p2 else p2

    price_rule = rules_for_round(group.round_number)['price']
    group.price = loser.bid if price_rule == 'second' else winner.bid
    group.winner_id_in_group = winner.id_in_group

    winner.payoff = max(cu(0), winner.valuation - group.price)
    loser.payoff = cu(0)


