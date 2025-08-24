# experiment1/pages.py
from otree.api import *
from .models import (
    C, Player, Group, Subsession,
    set_payoffs, phase_and_round_in_session, rules_for_round, price_label_for_round
)

def _common_context(page):
    s_no, r_in_s = phase_and_round_in_session(page.round_number)
    rules = rules_for_round(page.round_number)
    return dict(
        session_no=s_no,
        round_in_session=r_in_s,
        ROUNDS_PER_SESSION=C.ROUNDS_PER_SESSION,
        price_rule=price_label_for_round(page.round_number),
        matching=rules['matching'],
        tie_rule='random',
        chat=rules['chat'],
    )

class Instructions(Page):
    def vars_for_template(self):
        ctx = _common_context(self)
        ctx['ROUNDS'] = C.ROUNDS_PER_SESSION
        return ctx

class Bid(Page):
    form_model = 'player'
    form_fields = ['bid']
    timeout_seconds = 60
    timeout_submission = {'bid': cu(0)}

    def vars_for_template(self):
        ctx = _common_context(self)
        # valuation was set in creating_session; simply pass it through
        ctx['valuation'] = self.player.valuation
        return ctx

class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs

class Results(Page):
    def vars_for_template(self):
        opp = self.player.get_others_in_group()[0]
        you_won = (self.group.winner_id_in_group == self.player.id_in_group)
        return dict(
            **_common_context(self),
            your_bid=self.player.bid,
            opp_bid=opp.bid,
            valuation=self.player.valuation,
            price=self.group.price,
            you_won=you_won,
        )

page_sequence = [Instructions, Bid, ResultsWaitPage, Results]

