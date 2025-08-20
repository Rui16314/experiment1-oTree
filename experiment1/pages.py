# experiment1/pages.py
from otree.api import *
from .models import C, cu  # cu imported for safe defaulting


class Instructions(Page):
    def is_displayed(self):
        return self.round_number == 1


class Bid(Page):
    form_model = "player"
    form_fields = ["bid"]
    timeout_seconds = 60

    # Seed a valuation for THIS round before the page renders.
    def get_form_fields(self):
        import random
        if self.player.valuation is None:
            self.player.valuation = cu(round(random.uniform(0, 100), 2))
        return self.form_fields

    def vars_for_template(self):
        # Defensive read: never let a None reach the template.
        v = self.player.valuation
        if v is None:
            import random
            v = cu(round(random.uniform(0, 100), 2))
            self.player.valuation = v
        return dict(
            valuation=v,
            round_number=self.round_number,
            total_rounds=C.NUM_ROUNDS,
        )

    def before_next_page(self, timeout_happened):
        self.player.submitted = (not timeout_happened) and (self.player.bid is not None)
        # If you prefer to force a numeric bid on timeout, uncomment:
        # if timeout_happened or self.player.bid is None:
        #     self.player.bid = cu(0)


class ResultsWaitPage(WaitPage):
    after_all_players_arrive = "set_payoffs"


class Results(Page):
    def vars_for_template(self):
        v = self.player.valuation
        return dict(
            valuation=v if v is not None else cu(0),
            price=self.group.price,
            is_winner=(self.group.winner_id_in_group == self.player.id_in_group),
            payoff=self.player.payoff,
        )


page_sequence = [Instructions, Bid, ResultsWaitPage, Results]

