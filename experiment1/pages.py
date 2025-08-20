# experiment1/pages.py
from otree.api import *
from .models import C, Subsession, Group, Player, cu


class Instructions(Page):
    """Show only in round 1."""
    def is_displayed(self):
        return self.round_number == 1


class Bid(Page):
    form_model = "player"
    form_fields = ["bid"]
    timeout_seconds = 60

    # === IMPORTANT: seed a valuation for *this* round before the page renders ===
    def get_form_fields(self):
        # We don't *read* player.valuation here (reading None would raise);
        # we just *write* a fresh valuation each round to be bulletproof.
        import random
        self.player.valuation = cu(round(random.uniform(0, 100), 2))
        return self.form_fields

    def vars_for_template(self):
        # Accessing a None field raises in oTree, so be defensive.
        try:
            v = self.player.valuation  # may raise if still None
        except TypeError:
            v = None
        return dict(
            valuation=v,
            round_number=self.round_number,
            total_rounds=C.NUM_ROUNDS,
        )

    def before_next_page(self, timeout_happened):
        # Mark whether a bid was actually submitted (useful for your stats).
        self.player.submitted = not timeout_happened and self.player.bid is not None
        # If you prefer to force a numeric bid on timeout, uncomment next 2 lines:
        # if timeout_happened or self.player.bid is None:
        #     self.player.bid = cu(0)


class ResultsWaitPage(WaitPage):
    after_all_players_arrive = "set_payoffs"


class Results(Page):
    def vars_for_template(self):
        # Same defensive read pattern
        try:
            v = self.player.valuation
        except TypeError:
            v = None
        return dict(
            valuation=v,
            price=self.group.price,
            is_winner=(self.group.winner_id_in_group == self.player.id_in_group),
            payoff=self.player.payoff,
        )


page_sequence = [Instructions, Bid, ResultsWaitPage, Results]

