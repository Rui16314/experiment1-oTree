# experiment1/pages.py
from otree.api import *
from .models import (
    C, Player, Group, Subsession,
    set_payoffs, draw_valuation,
    rules_for_round, phase_and_round_in_session
)

ROUNDS_PER_SESSION = 10


def common_ctx(player: Player):
    s, r = phase_and_round_in_session(player.round_number)
    rule = rules_for_round(player.round_number)
    price_label = 'first-price' if rule['price'] == 'first' else 'second-price'
    return dict(
        session_no=s,
        round_in_session=r,
        price_rule=price_label,
        matching=rule['matching'],
        chat=rule['chat'],
        ROUNDS_PER_SESSION=ROUNDS_PER_SESSION,
    )


class Instructions(Page):
    # show at the start of each 10-round block
    def is_displayed(self):
        _, r = phase_and_round_in_session(self.round_number)
        return r == 1

    def vars_for_template(self):
        return common_ctx(self.player)


class Bid(Page):
    form_model = 'player'
    form_fields = ['bid']
    timeout_seconds = 60
    timeout_submission = {'bid': cu(0)}

    def vars_for_template(self):
        if self.player.valuation is None:
            self.player.valuation = draw_valuation()
        ctx = common_ctx(self.player)
        ctx.update(valuation=self.player.valuation)
        return ctx


class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs


class Results(Page):
    def vars_for_template(self):
        ctx = common_ctx(self.player)
        opp = self.player.get_others_in_group()[0]
        ctx.update(
            your_bid=self.player.bid,
            opp_bid=opp.bid,
            valuation=self.player.valuation,
            price=self.group.price,
            you_won=(self.group.winner_id_in_group == self.player.id_in_group),
        )
        return ctx


page_sequence = [Instructions, Bid, ResultsWaitPage, Results]

