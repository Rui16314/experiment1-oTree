# experiment1/models.py
from otree.api import *
from random import randint, choice


class C(BaseConstants):
    NAME_IN_URL = 'experiment1'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 60
    ROUNDS_PER_SESSION = 10  # 6 sessions × 10 rounds


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    # Winning price to pay, and the winner's id_in_group (0 if no winner)
    price = models.CurrencyField(initial=cu(0))
    winner_id_in_group = models.IntegerField(initial=0)


class Player(BasePlayer):
    valuation = models.CurrencyField()
    # Players may time out and not submit a bid -> leave blank=True
    bid = models.CurrencyField(min=0, max=100, blank=True)


# ----------------- helpers about sessions/rules -----------------

def session_and_round_in_session(round_number: int):
    """Return (session_no 1..6, round_in_session 1..10)."""
    s = (round_number - 1) // C.ROUNDS_PER_SESSION + 1
    r = (round_number - 1) % C.ROUNDS_PER_SESSION + 1
    return s, r


def rules_for_round(round_number: int):
    """Return dict with the auction rules for a given round."""
    s, _ = session_and_round_in_session(round_number)
    # Sessions 1–3: first price; 4–6: second price
    price_rule = 'first' if s <= 3 else 'second'
    # Sessions 1 & 4 random matching; others fixed within the 10-round block
    matching = 'random' if s in (1, 4) else 'fixed'
    # Sessions 3 & 6 allow chat (templates may use this info)
    chat = s in (3, 6)
    return dict(price_rule=price_rule, matching=matching, chat=chat)


def draw_valuation():
    # Uniform on 0–100 with 2 decimals
    return cu(randint(0, 10000) / 100)


# ----------------------------- oTree hooks -----------------------------

def creating_session(subsession: Subsession):
    """Group players and draw valuations each round."""
    s, r_in_s = session_and_round_in_session(subsession.round_number)
    r = rules_for_round(subsession.round_number)

    if r['matching'] == 'random':
        subsession.group_randomly()
    else:
        # Fixed partner inside the 10-round session block
        base_round = (s - 1) * C.ROUNDS_PER_SESSION + 1
        if r_in_s == 1:
            subsession.group_randomly()  # choose pairs at the start of the session
        else:
            subsession.group_like_round(base_round)

    # Each round, everyone gets a fresh valuation
    for p in subsession.get_players():
        p.valuation = draw_valuation()


def set_payoffs(group: Group):
    """Compute winner, price, and payoffs after both bids are (possibly) in."""
    p1, p2 = group.get_players()

    # Treat missing bids as -1 so the player always loses.
    b1 = p1.bid if p1.bid is not None else cu(-1)
    b2 = p2.bid if p2.bid is not None else cu(-1)

    # If nobody bid, there is no winner and no price.
    if b1 < 0 and b2 < 0:
        group.price = cu(0)
        group.winner_id_in_group = 0
        p1.payoff = cu(0)
        p2.payoff = cu(0)
        return

    # Determine winner (ties broken at random)
    if b1 > b2:
        winner, loser = p1, p2
    elif b2 > b1:
        winner, loser = p2, p1
    else:
        winner = choice([p1, p2])
        loser = p1 if winner is p2 else p2

    # Price rule by session
    price_rule = rules_for_round(group.round_number)['price_rule']
    if price_rule == 'first':
        price = winner.bid
    else:  # second-price
        # If the loser didn't bid (timeout), use 0 as the loser's bid for price
        price = loser.bid if loser.bid is not None else cu(0)

    group.price = price
    group.winner_id_in_group = winner.id_in_group

    # Payoffs
    winner.payoff = max(cu(0), winner.valuation - price)
    loser.payoff = cu(0)
# --- Chat storage ---
class ChatMessage(ExtraModel):
    group = models.Link(Group)
    sender_id_in_group = models.IntegerField()
    text = models.LongStringField()
    ts = models.FloatField()  # filled from pages.py

def chat_history_for(group):
    rows = ChatMessage.filter(group=group).order_by('id')  # id gives correct order
    return [{'sid': r.sender_id_in_group, 'text': r.text, 'ts': r.ts} for r in rows]



