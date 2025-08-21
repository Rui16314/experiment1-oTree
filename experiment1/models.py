from otree.api import *
import random

# Short alias for Currency
cu = Currency  # (so we can write cu(0))

class C(BaseConstants):
    NAME_IN_URL = 'experiment1'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 10
    # session.config may override these, but we keep sensible defaults:
    PRICE_RULE = 'first'     # 'first' or 'second'
    MATCHING   = 'random'    # 'random' or 'fixed' (fixed = like round 1)
    TIE_RULE   = 'random'    # 'random' or 'lowest_id'


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    price = CurrencyField(initial=cu(0))
    winner_id_in_group = IntegerField(initial=0)


class Player(BasePlayer):
    valuation = CurrencyField()                 # set each round
    bid       = CurrencyField(blank=True)       # may be blank if timeout
    submitted = BooleanField(initial=False)


# ----------- helpers -----------

def _session_opt(session, key, default):
    v = session.config.get(key)
    return (v or default).lower() if isinstance(v, str) else (v if v is not None else default)


# ----------- round setup -----------

def creating_session(subsession: Subsession):
    """Assign groups and valuations at the start of each round."""
    s = subsession.session

    # grouping
    matching = _session_opt(s, 'matching', C.MATCHING)
    if subsession.round_number == 1 or matching == 'random':
        subsession.group_randomly()
    else:
        subsession.group_like_round(1)

    # independent private values in [0, 100]
    for p in subsession.get_players():
        # uniform(0,100) with cents; cast to Currency
        p.valuation = cu(round(random.uniform(0, 100), 2))


# ----------- payoff logic -----------

def set_payoffs(group: Group):
    """Robust against missing bids/valuations so the wait page can never crash."""
    p1, p2 = group.get_players()

    # Ensure valuations exist (paranoia guard)
    for p in (p1, p2):
        if p.valuation is None:
            p.valuation = cu(0)
        if p.bid is None:
            # If player timed out, treat as a zero bid.
            p.bid = cu(0)

    # Determine winner (highest bid), with a tie rule
    if p1.bid > p2.bid:
        winner, loser = p1, p2
    elif p2.bid > p1.bid:
        winner, loser = p2, p1
    else:
        tie_rule = _session_opt(group.session, 'tie_rule', C.TIE_RULE)
        if tie_rule == 'lowest_id':
            winner, loser = (p1, p2) if p1.id_in_group < p2.id_in_group else (p2, p1)
        else:
            winner, loser = random.choice([(p1, p2), (p2, p1)])

    # Price rule
    price_rule = _session_opt(group.session, 'price_rule', C.PRICE_RULE)
    price = winner.bid if price_rule == 'first' else loser.bid

    # Record outcomes
    group.price = price
    group.winner_id_in_group = winner.id_in_group

    # Payoffs
    winner.payoff = max(cu(0), winner.valuation - price)
    loser.payoff = cu(0)

