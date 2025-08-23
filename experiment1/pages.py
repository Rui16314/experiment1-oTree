# experiment1/pages.py
from otree.api import *
from .models import (
    C, Player, Group, Subsession,
    set_payoffs, rules_for_round, phase_and_round_in_session, draw_valuation
)

def price_label_for_round(round_number: int) -> str:
    """Return 'first-price' or 'second-price' for this round."""
    return 'first-price' if rules_for_round(round_number)['price'] == 'first' else 'second-price'


class Instructions(Page):
    """
    Show instructions at the start of EACH 10-round session block
    (i.e., rounds 1, 11, 21, 31, 41, 51).
    """
    def is_displayed(self):
        _, round_in_session = phase_and_round_in_session(self.round_number)
        return round_in_session == 1

    def vars_for_template(self):
        s_no, r_in_s = phase_and_round_in_session(self.round_number)
        r = rules_for_round(self.round_number)
        return dict(
            # for your instruction partials
            ROUNDS=10,                               # rounds per session (fixed)
            session_no=s_no,                         # 1..6
            round_in_session=r_in_s,                 # 1..10
            price_rule=price_label_for_round(self.round_number),
            matching=r['matching'],                  # 'random' or 'fixed'
            tie_rule='random',                       # keep simple unless you add options
            chat=r['chat'],                          # True/False
        )


class Bid(Page):
    form_model = 'player'
    form_fields = ['bid']
    timeout_seconds = 60
    timeout_submission = {'bid': cu(0)}

    def vars_for_template(self):
        # SAFETY: if for any reason valuation didn't get set, create one here.
        if self.player.valuation is None:
            self.player.valuation = draw_valuation()

        s_no, r_in_s = phase_and_round_in_session(self.round_number)
        # If your Bid.html still checks `{% if timeout_seconds %}` add it explicitly:
        timeout = self.get_timeout_seconds()

        return dict(
            valuation=self.player.valuation,
            session_no=s_no,
            round_in_session=r_in_s,
            timeout_seconds=timeout,
        )


class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs


class Results(Page):
    def vars_for_template(self):
        opp = self.player.get_others_in_group()[0]
        s_no, r_in_s = phase_and_round_in_session(self.round_number)
        return dict(
            your_bid=self.player.bid,
            opp_bid=opp.bid,
            valuation=self.player.valuation,
            price=self.group.price,
            you_won=(self.group.winner_id_in_group == self.player.id_in_group),
            session_no=s_no,
            round_in_session=r_in_s,
        )


page_sequence = [Instructions, Bid, ResultsWaitPage, Results]

