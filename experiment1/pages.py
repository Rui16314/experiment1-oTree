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

    def before_next_page(self, timeout_happened):
        """
        Draw a valuation for round 1 so the first Bid page always has a value.
        (Later rounds are drawn in creating_session; the Bid guard below
        also handles any missed cases robustly.)
        """
        import random
        from otree.api import Currency as cu
        # Only set if missing (safe write)
        if self.player.__dict__.get('valuation') is None:
            self.player.valuation = cu(round(random.uniform(0, 100), 2))


class Bid(Page):
    form_model = 'player'
    form_fields = ['bid']
    timeout_seconds = 60

    def _ensure_valuation(self):
        """
        IMPORTANT: Do NOT read self.player.valuation before it's set.
        Access the raw storage (instance.__dict__) first; if it's None,
        set it, then it's safe to read self.player.valuation.
        """
        raw = self.player.__dict__.get('valuation')
        if raw is None:
            import random
            from otree.api import Currency as cu
            self.player.valuation = cu(round(random.uniform(0, 100), 2))

    def vars_for_template(self):
        # Guarantee valuation exists without triggering the None access error.
        self._ensure_valuation()
        return dict(valuation=self.player.valuation)

    def before_next_page(self, timeout_happened):
        self.player.submitted = not timeout_happened
        if timeout_happened:
            self.player.bid = None


class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs


class Results(Page):
    def vars_for_template(self):
        p = self.player
        g = p.group
        opp = p.get_others_in_group()[0]
        return dict(
            my_val=p.valuation,
            my_bid=p.bid,
            opp_val=opp.valuation,
            opp_bid=opp.bid,
            price=g.price,
            i_won=(g.winner_id_in_group == p.id_in_group),
            my_payoff=p.payoff,
        )


class SessionSummary(Page):
    def is_displayed(self):
        return self.player.round_number == C.NUM_ROUNDS

    def vars_for_template(self):
        import json
        subsession = self.subsession

        # Average bid by valuation bin
        BIN = 10
        n_bins = max(1, int(100 / BIN))
        labels = [f"{i*BIN}-{i*BIN+BIN-1}" for i in range(n_bins)]
        sums = [0.0] * n_bins
        counts = [0] * n_bins

        for r in range(1, C.NUM_ROUNDS + 1):
            for p in subsession.in_round(r).get_players():
                # Skip missing entries safely
                if p.__dict__.get('valuation') is None or p.bid is None:
                    continue
                v = float(p.valuation)
                b = float(p.bid)
                k = min(int(v // BIN), n_bins - 1)
                sums[k] += b
                counts[k] += 1

        avg_by_bin = [(s / c if c > 0 else 0) for s, c in zip(sums, counts)]

        # Average revenue by round
        rounds = list(range(1, C.NUM_ROUNDS + 1))
        avg_rev_by_round = []
        for r in rounds:
            prices = [float(g.price or 0) for g in subsession.in_round(r).get_groups()]
            avg_rev_by_round.append(sum(prices) / len(prices) if prices else 0)

        overall_rev = sum(avg_rev_by_round) / len(avg_rev_by_round) if avg_rev_by_round else 0

        return dict(
            labels_bins_json=json.dumps(labels),
            avg_bid_bins_json=json.dumps(avg_by_bin),
            rounds_json=json.dumps(rounds),
            avg_rev_by_round_json=json.dumps(avg_rev_by_round),
            avg_rev_overall=overall_rev,
            bin_size=BIN,
        )


page_sequence = [
    Instructions,
    Bid,
    ResultsWaitPage,
    Results,
    SessionSummary,
]

