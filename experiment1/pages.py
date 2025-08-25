# experiment1/pages.py
from otree.api import *
from .models import C, set_payoffs, rules_for_round, session_and_round_in_session, draw_valuation

class Instructions(Page):
    """Shown once per session (rounds 1, 11, 21, 31, 41, 51)."""
    def is_displayed(self):
        _, ris = session_and_round_in_session(self.round_number)
        return ris == 1

    def vars_for_template(self):
        s_no, _ = session_and_round_in_session(self.round_number)
        r = rules_for_round(self.round_number)
        # Pick which session-specific include to render
        template_key = {
            1: 'S1_First',
            2: 'S2_FirstRepeated',
            3: 'S3_FirstRepeated_Chat',
            4: 'S4_Second',
            5: 'S5_SecondRepeated',
            6: 'S6_SecondRepeated_Chat',
        }[s_no]
        return dict(
            session_no=s_no,
            include_name=f"experiment1/Instructions_{template_key}.html",
            show_general=(s_no == 1),   # show general instructions only before Session 1
        )


class Bid(Page):
    form_model = 'player'
    form_fields = ['bid']
    timeout_seconds = 60
    timeout_submission = {'bid': cu(0)}  # auto-bid if time runs out

    # Defensive: make sure valuation exists at render time (e.g., after DB reset)
    def _ensure_valuation(self):
        if self.player.valuation is None:
            self.player.valuation = draw_valuation()

    def vars_for_template(self):
        self._ensure_valuation()
        s_no, ris = session_and_round_in_session(self.round_number)
        return dict(
            session_no=s_no,
            round_in_session=ris,
            ROUNDS_PER_SESSION=C.ROUNDS_PER_SESSION,
            valuation=self.player.valuation,
        )


class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs


class Results(Page):
    def vars_for_template(self):
        opp = self.player.get_others_in_group()[0]
        s_no, ris = session_and_round_in_session(self.round_number)
        you_won = (self.group.winner_id_in_group == self.player.id_in_group)
        return dict(
            session_no=s_no,
            round_in_session=ris,
            ROUNDS_PER_SESSION=C.ROUNDS_PER_SESSION,
            your_bid=self.player.bid,
            opp_bid=opp.bid,
            price=self.group.price,
            valuation=self.player.valuation,
            you_won=you_won,
        )


page_sequence = [Instructions, Bid, ResultsWaitPage, Results]



