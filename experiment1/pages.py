# experiment1/pages.py
from otree.api import *
from .models import (
    C, set_payoffs, draw_valuation,
    phase_and_round_in_session, rules_for_round
)

ROUNDS_PER_SESSION = 10

def price_label_for_round(rn: int) -> str:
    return 'first-price' if rules_for_round(rn)['price'] == 'first' else 'second-price'

class Instructions(Page):
    def vars_for_template(self):
        s_no, r_in_s = phase_and_round_in_session(self.round_number)
        r = rules_for_round(self.round_number)
        return dict(
            ROUNDS_PER_SESSION=ROUNDS_PER_SESSION,
            session_no=s_no,
            round_in_session=r_in_s,
            price_rule=price_label_for_round(self.round_number),
            matching=r['matching'],
            chat=r['chat'],
            tie_rule='random',
        )

class Bid(Page):
    form_model = 'player'
    form_fields = ['bid']
    timeout_seconds = 60
    timeout_submission = {'bid': cu(0)}

    def _ensure_valuation(self):
        # Make this page robust even if a legacy row has NULL valuation.
        if self.player.valuation is None:
            self.player.valuation = draw_valuation()

    def vars_for_template(self):
        self._ensure_valuation()
        s_no, r_in_s = phase_and_round_in_session(self.round_number)
        return dict(
            ROUNDS_PER_SESSION=ROUNDS_PER_SESSION,
            session_no=s_no,
            round_in_session=r_in_s,
            valuation=self.player.valuation,
        )

class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs

class Results(Page):
    def vars_for_template(self):
        s_no, r_in_s = phase_and_round_in_session(self.round_number)
        opp = self.player.get_others_in_group()[0]
        you_won = (self.group.winner_id_in_group == self.player.id_in_group)
        return dict(
            ROUNDS_PER_SESSION=ROUNDS_PER_SESSION,
            session_no=s_no,
            round_in_session=r_in_s,
            your_bid=self.player.bid,
            opp_bid=opp.bid,
            valuation=self.player.valuation,
            price=self.group.price,
            you_won=you_won,
        )

page_sequence = [Instructions, Bid, ResultsWaitPage, Results]



