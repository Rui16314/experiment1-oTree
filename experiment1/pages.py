# experiment1/pages.py
from otree.api import *
from .models import C, Player, Group, Subsession, set_payoffs, draw_valuation

ROUNDS_PER_SESSION = 10

def common_ctx(player: Player):
    r = player.round_number
    return dict(
        ROUNDS=ROUNDS_PER_SESSION,
        session_num=((r - 1) // ROUNDS_PER_SESSION) + 1,
        round_in_session=((r - 1) % ROUNDS_PER_SESSION) + 1,
    )

class Instructions(Page):
    def vars_for_template(self):
        ctx = common_ctx(self.player)
        ctx.update(dict(
            price_rule='first-price',
            matching='random',
            tie_rule='random',
            chat=False,
        ))
        return ctx

class Bid(Page):
    form_model = 'player'
    form_fields = ['bid']
    timeout_seconds = 60
    timeout_submission = {'bid': cu(0)}

    def vars_for_template(self):
        if self.player.valuation is None:
            self.player.valuation = draw_valuation()
        ctx = common_ctx(self.player)
        ctx.update(dict(valuation=self.player.valuation))
        return ctx

class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs

class Results(Page):
    def vars_for_template(self):
        ctx = common_ctx(self.player)
        opp = self.player.get_others_in_group()[0]
        you_won = (self.group.winner_id_in_group == self.player.id_in_group)
        ctx.update(dict(
            your_bid=self.player.bid,
            opp_bid=opp.bid,
            valuation=self.player.valuation,
            price=self.group.price,
            you_won=you_won,
        ))
        return ctx

page_sequence = [Instructions, Bid, ResultsWaitPage, Results]


