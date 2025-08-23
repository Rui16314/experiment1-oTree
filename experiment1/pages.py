# experiment1/pages.py
from otree.api import *
from .models import C, Player, Group, Subsession, set_payoffs, draw_valuation

def _common_ctx(page):
    """Context shared by pages that show instructions text."""
    s = page.session
    return dict(
        price_rule='first-price',          # keep simple for now
        matching='random',
        tie_rule='random',
        chat=False,
        ROUNDS=C.NUM_ROUNDS,               # 10
        session_no=s.config.get('session_no', 1),     # default to 1
        round_in_session=page.round_number            # 1..10 in this app
    )

class Instructions(Page):
    def vars_for_template(self):
        return _common_ctx(self)

class Bid(Page):
    form_model = 'player'
    form_fields = ['bid']
    timeout_seconds = 60
    timeout_submission = {'bid': cu(0)}

    def vars_for_template(self):
        # make sure valuation exists
        if self.player.valuation is None:
            self.player.valuation = draw_valuation()
        ctx = dict(valuation=self.player.valuation)
        # optional: include shared fields if your Bid.html needs them later
        ctx.update(_common_ctx(self))
        return ctx

class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs

class Results(Page):
    def vars_for_template(self):
        opp = self.player.get_others_in_group()[0]
        return dict(
            your_bid=self.player.bid,
            opp_bid=opp.bid,
            valuation=self.player.valuation,
            price=self.group.price,
            you_won=(self.group.winner_id_in_group == self.player.id_in_group),
        )

page_sequence = [Instructions, Bid, ResultsWaitPage, Results]
