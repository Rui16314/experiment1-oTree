# experiment1/pages.py
from otree.api import *
from otree.api import Currency as cu
from .models import C, Player, Group, Subsession, set_payoffs, draw_valuation

class Instructions(Page):
    def vars_for_template(self):
        s = self.session
        return dict(
            price_rule='first-price',      # keep simple for now
            matching='random',
            tie_rule='random',
            chat=False,
            ROUNDS=C.NUM_ROUNDS,
        )

class Bid(Page):
    form_model = 'player'
    form_fields = ['bid']
    timeout_seconds = 60
    timeout_submission = {'bid': cu(0)}

    def vars_for_template(self):
        # Safety: ensure valuation exists
        if self.player.valuation is None:
            self.player.valuation = draw_valuation()
        return dict(valuation=self.player.valuation)

class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs

class Results(Page):
    def is_displayed(self):
        return True  # or: return self.group.price is not None

    def vars_for_template(self):
        opp = self.player.get_others_in_group()[0]
        you_won = (self.group.winner_id_in_group == self.player.id_in_group)
        return dict(
            your_bid=self.player.bid,
            opp_bid=opp.bid,
            valuation=self.player.valuation,
            price=self.group.price,
            you_won=you_won,
        )

page_sequence = [Instructions, Bid, ResultsWaitPage, Results]

