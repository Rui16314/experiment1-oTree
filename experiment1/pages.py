from otree.api import *
from .models import C, Player, Group, Subsession, set_payoffs, cu


def price_label(session):
    pr = (session.config.get('price_rule') or 'first').lower()
    return 'first-price' if pr == 'first' else 'second-price'


class Instructions(Page):
    def vars_for_template(player: Player):
        s = player.session
        return dict(
            price_rule=price_label(s),
            matching=(s.config.get('matching') or 'random').lower(),
            tie_rule=(s.config.get('tie_rule') or 'random').lower(),
            ROUNDS=C.NUM_ROUNDS,
            chat=bool(s.config.get('chat', False)),
        )


class Bid(Page):
    form_model = 'player'
    form_fields = ['bid']
    timeout_seconds = 60
    # If they time out, store a zero bid so payoff code never sees None.
    timeout_submission = {'bid': cu(0)}

    def vars_for_template(player: Player):
        # Keep template simple; valuation is guaranteed non-None by creating_session
        return dict(valuation=player.valuation)


class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs


class Results(Page):
    def vars_for_template(player: Player):
        other = player.get_others_in_group()[0]
        group = player.group
        return dict(
            your_bid   = player.bid,
            opp_bid    = other.bid,
            valuation  = player.valuation,
            price      = group.price,
            you_won    = (group.winner_id_in_group == player.id_in_group),
        )


page_sequence = [Instructions, Bid, ResultsWaitPage, Results]

# pages.py  (add these imports at the top)
from statistics import mean
import math

# ---------- helpers ----------
def _all_players_in_session(session):
    # players from every round of this session
    return [p for ss in session.get_subsessions() for p in ss.get_players()]

def _avg_bid_by_bucket(players, bucket_size=10):
    """
    Return (xs, ys) where xs are bucket start values (0,10,20,...)
    and ys are average bids for players whose valuation fell in the bucket.
    """
    buckets = {i: [] for i in range(0, 100, bucket_size)}
    for p in players:
        if p.bid is None or p.valuation is None:
            continue
        v = float(p.valuation)
        b = float(p.bid)
        key = int(min(99, max(0, math.floor(v))))  # clamp 0..99
        key = (key // bucket_size) * bucket_size
        buckets[key].append(b)

    xs = sorted(buckets.keys())
    ys = [round(mean(buckets[x]), 2) if buckets[x] else None for x in xs]
    return xs, ys

def _avg_bid_for_value(players, target_value, tol=0.5):
    """Average bid when valuation ≈ target_value (e.g., exactly 50)."""
    vals = [float(p.bid) for p in players
            if p.bid is not None and p.valuation is not None
            and abs(float(p.valuation) - target_value) <= tol]
    return round(mean(vals), 2) if vals else None

def _avg_bid_for_range(players, lo, hi):
    """Average bid when valuation in [lo, hi]"""
    vals = [float(p.bid) for p in players
            if p.bid is not None and p.valuation is not None
            and lo <= float(p.valuation) <= hi]
    return round(mean(vals), 2) if vals else None

def _revenue_by_round(session):
    """Average winning price per round across all groups."""
    points = []
    for ss in session.get_subsessions():
        prices = [float(g.price) for g in ss.get_groups() if g.price is not None]
        points.append(round(mean(prices), 2) if prices else None)
    return points  # index 0 => round 1

def _per_player_series(session):
    """
    For each participant in THIS session, produce a (label, xs, ys) where
    xs = valuations encountered (binned to int), ys = average bid at that valuation.
    """
    series = []
    # map participant_code -> all Player rows for that participant
    by_participant = {}
    for p in _all_players_in_session(session):
        by_participant.setdefault(p.participant.code, []).append(p)

    for code, plist in by_participant.items():
        label = plist[0].participant.label or plist[0].id_in_subsession  # fallback
        bucket = {}
        for p in plist:
            if p.bid is None or p.valuation is None:
                continue
            v = int(round(float(p.valuation)))  # 0..100
            bucket.setdefault(v, []).append(float(p.bid))
        xs = sorted(bucket.keys())
        ys = [round(mean(bucket[x]), 2) for x in xs]
        series.append(dict(label=str(label), xs=xs, ys=ys))
    return series

# ---------- summary page ----------
class SessionSummary(Page):
    """Charts after the last round."""
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS

    def vars_for_template(player: Player):
        session = player.session
        everyone = _all_players_in_session(session)

        # 1) Average bidding behavior across all players, by valuation buckets (10-wide)
        bucket_x, bucket_y = _avg_bid_by_bucket(everyone, bucket_size=10)

        # 1a) example point: valuation exactly 50
        avg_at_50 = _avg_bid_for_value(everyone, 50)

        # 1b) example bar: valuations 30–39
        avg_30_39 = _avg_bid_for_range(everyone, 30, 39)

        # 2) Per-student series (one chart per student)
        per_player = _per_player_series(session)

        # 3) Average revenue by round (winning price)
        rev_by_round = _revenue_by_round(session)  # length = NUM_ROUNDS
        # 4) Average revenue overall
        rev_overall = round(
            mean([r for r in rev_by_round if r is not None]), 2
        ) if any(rev_by_round) else None

        return dict(
            bucket_x=bucket_x, bucket_y=bucket_y,
            avg_at_50=avg_at_50,
            avg_30_39=avg_30_39,
            per_player=per_player,
            rev_by_round=rev_by_round,
            rev_overall=rev_overall,
        )

# Add this page at the very END of your sequence:
page_sequence = [
    Instructions,
    Bid,
    ResultsWaitPage,
    Results,
    SessionSummary,   # <---- NEW
]
