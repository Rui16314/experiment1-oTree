from otree.api import *
from .models import C, set_payoffs, rules_for_round, phase_and_round_in_session


class Instructions(Page):
    # show only at the start of each 10-round session
    def is_displayed(self):
        _, r_in_s = phase_and_round_in_session(self.round_number)
        return r_in_s == 1

    def vars_for_template(self):
        s_no, r_in_s = phase_and_round_in_session(self.round_number)
        r = rules_for_round(self.round_number)
        return dict(
            ROUNDS_PER_SESSION=C.ROUNDS_PER_SESSION,
            session_no=s_no,
            round_in_session=r_in_s,
            price_rule=r['price'],               # 'first' or 'second'
            matching=r['matching'],              # 'random' or 'fixed'
            chat=r['chat'],                      # True/False
        )


class Bid(Page):
    form_model = 'player'
    form_fields = ['bid']
    timeout_seconds = 60  # 1 minute

    # never read a possibly-null field directly; always ensure first
    def _ensure_valuation(self):
        if self.player.field_maybe_none('valuation') is None:
            # extremely defensive: should already be set in creating_session
            from .models import draw_valuation
            self.player.valuation = draw_valuation()

    def vars_for_template(self):
        self._ensure_valuation()
        s_no, r_in_s = phase_and_round_in_session(self.round_number)
        return dict(
            ROUNDS_PER_SESSION=C.ROUNDS_PER_SESSION,
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
            ROUNDS_PER_SESSION=C.ROUNDS_PER_SESSION,
            session_no=s_no,
            round_in_session=r_in_s,
            your_bid=self.player.bid,
            opp_bid=opp.bid,
            valuation=self.player.valuation,
            price=self.group.price,
            you_won=you_won,
        )


page_sequence = [Instructions, Bid, ResultsWaitPage, Results]



