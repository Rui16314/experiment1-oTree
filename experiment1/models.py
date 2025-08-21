from otree.api import *
import random


class C(BaseConstants):
    NAME_IN_URL = 'experiment1'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 10


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    # realized price this round (depends on price rule & bids)
    price = models.CurrencyField(initial=0)
    # 1 or 2 if there is a winner; 0 if no sale
    winner_id_in_group = models.IntegerField(initial=0)


class Player(BasePlayer):
    # private value in [0,100] (currency points)
    valuation = models.CurrencyField()
    # player’s bid (can be blank if they time out)
    bid = models.CurrencyField(min=0, max=100, blank=True)


# ----- Helpers ---------------------------------------------------------------

def _price_rule(session):
    # 'first' or 'second'
    return (session.config.get('price_rule') or 'first').lower()


def _matching_rule(session):
    # 'random' (re-draw pairs each round) or 'fixed' (keep round 1 pairs)
    return (session.config.get('matching') or 'random').lower()


def _tie_rule(session):
    # 'random' (randomly choose winner) or 'split' (split surplus)
    return (session.config.get('tie_rule') or 'random').lower()


# ----- Session / Round setup -------------------------------------------------

def creating_session(subsession: Subsession):
    """Runs once per round. Sets pairing & valuations for that round."""
    s = subsession.session

    # Pairing
    if subsession.round_number == 1:
        subsession.group_randomly()
    else:
        if _matching_rule(s) == 'random':
            subsession.group_randomly()
        else:
            subsession.group_like_round(1)  # keep the initial pairs

    # Draw private values independently U[0,100]
    for p in subsession.get_players():
        p.valuation = cu(round(random.uniform(0, 100), 2))


# ----- Outcome / Payoffs -----------------------------------------------------

def set_payoffs(group: Group):
    """Compute winner, price, and payoffs based on rule & bids."""
    s = group.session
    players = group.get_players()
    p1, p2 = players

    b1, b2 = p1.bid, p2.bid
    rule = _price_rule(s)
    tie = _tie_rule(s)

    # If both missed the page (both bids None) -> no trade
    if b1 is None and b2 is None:
        p1.payoff = cu(0)
        p2.payoff = cu(0)
        group.price = cu(0)
        group.winner_id_in_group = 0
        return

    # Treat None as an extremely low bid (i.e., can't win)
    c1 = float(b1) if b1 is not None else -1
    c2 = float(b2) if b2 is not None else -1

    # Determine (winner, loser)
    if c1 > c2:
        winner, loser = p1, p2
        winning_bid, losing_bid = b1, b2
    elif c2 > c1:
        winner, loser = p2, p1
        winning_bid, losing_bid = b2, b1
    else:
        # c1 == c2 (including both 0 or both >=0)
        if tie == 'split':
            # split the surplus at the common bid
            common_bid = b1 if b1 is not None else b2 if b2 is not None else cu(0)
            # If both None, treat as 0
            if common_bid is None:
                common_bid = cu(0)
            p1.payoff = max(cu(0), (p1.valuation - common_bid) / 2)
            p2.payoff = max(cu(0), (p2.valuation - common_bid) / 2)
            group.price = common_bid
            group.winner_id_in_group = 0  # denote split
            return
        else:
            # tie == 'random'
            winner, loser = random.choice([(p1, p2), (p2, p1)])
            winning_bid = b1 if winner is p1 else b2
            losing_bid = b2 if winner is p1 else b1

    # Price rule
    if rule == 'second':
        # pay the highest *other* bid (if None -> 0)
        price = losing_bid if losing_bid is not None else cu(0)
    else:
        # 'first' price: pay your own bid (if None -> 0, but winner can't be None here)
        price = winning_bid if winning_bid is not None else cu(0)

    # Apply payoffs
    group.price = price
    group.winner_id_in_group = winner.id_in_group
    winner.payoff = max(cu(0), winner.valuation - price)
    loser.payoff = cu(0)

