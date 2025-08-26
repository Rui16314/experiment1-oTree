# experiment1/pages.py
from otree.api import *
from .models import (
    C, Subsession, Group, Player,
    phase_and_round_in_session, rules_for_round, set_payoffs
)


class Instructions(Page):
    """Show once at the start of each 10-round session, not every round."""
    def is_displayed(self):
        _, r_in_s = phase_and_round_in_session(self.round_number)
        return r_in_s == 1

    def vars_for_template(self):
        s_no, r_in_s = phase_and_round_in_session(self.round_number)
        r = rules_for_round(self.round_number)
        return dict(
            session_no=s_no,
            round_in_session=r_in_s,
            ROUNDS_PER_SESSION=C.ROUNDS_PER_SESSION,
            price_rule=r['price_rule'],    # 'first' or 'second'
            matching=r['matching'],        # 'random' or 'fixed'
            chat=r['chat'],                # True/False
        )


class Bid(Page):
    form_model = 'player'
    form_fields = ['bid']

    def get_timeout_seconds(self):
        # 60-second limit (adjust if needed)
        return 60

    def before_next_page(self, timeout_happened):
        # Auto-bid rule: if time runs out, set bid = valuation/2
        if timeout_happened and self.player.field_maybe_none('bid') is None:
            self.player.bid = self.player.valuation / 2


class ResultsWait(WaitPage):
    after_all_players_arrive = set_payoffs


class Results(Page):
    def vars_for_template(self):
        s_no, r_in_s = phase_and_round_in_session(self.round_number)
        opp = self.player.get_others_in_group()[0]
        return dict(
            session_no=s_no,
            round_in_session=r_in_s,
            ROUNDS_PER_SESSION=C.ROUNDS_PER_SESSION,
            valuation=self.player.valuation,
            your_bid=self.player.field_maybe_none('bid'),
            opp_bid=opp.field_maybe_none('bid'),
            price=self.group.price,
            you_won=(self.group.winner_id_in_group == self.player.id_in_group),
        )


page_sequence = [Instructions, Bid, ResultsWait, Results]


