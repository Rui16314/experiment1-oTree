# experiment1/pages.py
from otree.api import *
from .models import C, set_payoffs


class Instructions(Page):
    def is_displayed(self):
        return self.player.round_number == 1

    def vars_for_template(self):
        return dict(
            price_rule=C.PRICE_RULE,
            matching=C.MATCHING,
        )


class Bid(Page):
    form_model = 'player'
    form_fields = ['bid']
    timeout_seconds = 60

    def vars_for_template(self):
        return dict(valuation=self.player.valuation)

    def before_next_page(self, timeout_happened):
        self.player.submitted = not timeout_happened
        if timeout_happened:
            self.player.bid = None


class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs


class Results(Page):
    def vars_for_template(self):
        player = self.player
        opp = player.get_others_in_group()[0]
        g = player.group
        return dict(
            my_val=player.valuation,
            my_bid=player.bid,
            opp_val=opp.valuation,
            opp_bid=opp.bid,
            price=g.price,
            i_won=(g.winner_id_in_group == player.id_in_group),
            my_payoff=player.payoff,
        )


class SessionSummary(Page):
    def is_displayed(self):
        return self.player.round_number == C.NUM_ROUNDS

    def vars_for_template(self):
        # build the summary data
        import json
        subsession = self.subsession
        BIN = 10
        pts = []
        for r in range(1, self.player.round_number + 1):
            for p in subsession.in_round(r).get_players():
                if p.bid is not None:
                    pts.append((float(p.valuation), float(p.bid)))

        n_bins = max(1, int(100 / BIN))
        labels = [f"{i*BIN}-{i*BIN+BIN-1}" for i in range(n_bins)]
        sums = [0.0] * n_bins
        counts = [0] * n_bins
        for v, b in pts:
            k = min(int(v // BIN), n_bins - 1)
            sums[k] += b
            counts[k] += 1
        avg = [(s / c if c > 0 else 0) for s, c in zip(sums, counts)]

        rounds = list(range(1, self.player.round_number + 1))
        rev = []
        for r in rounds:
            prices = [float(g.price or 0) for g in subsession.in_round(r).get_groups()]
            rev.append(sum(prices) / len(prices) if prices else 0)
        overall = sum(rev) / len(rev) if rev else 0

        return dict(
            labels_bins_json=json.dumps(labels),
            avg_bid_bins_json=json.dumps(avg),
            rounds_json=json.dumps(rounds),
            avg_rev_by_round_json=json.dumps(rev),
            avg_rev_overall=overall,
            bin_size=BIN,
        )


page_sequence = [Instructions, Bid, ResultsWaitPage, Results, SessionSummary]
