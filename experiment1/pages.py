# experiment1/pages.py
from otree.api import *
from .models import C, set_payoffs, rules_for_round, phase_and_round_in_session, draw_valuation

class BasePage(Page):
    def _ensure_valuation(self):
        # SAFE read: returns None instead of raising if the field is null
        val = self.player.field_maybe_none('valuation')
        if val is None:
            self.player.valuation = draw_valuation()
            self.player.save()
            val = self.player.valuation
        return val

class Instructions(BasePage):
    def vars_for_template(self):
        s_no, r_in_s = phase_and_round_in_session(self.round_number)
        r = rules_for_round(self.round_number)
        return dict(
            session_no=s_no,
            round_in_session=r_in_s,
            ROUNDS_PER_SESSION=10,
            price_rule='first-price' if r['price'] == 'first' else 'second-price',
            matching=r['matching'],
            chat=r['chat'],
        )

class Bid(BasePage):
    form_model = 'player'
    form_fields = ['bid']
    timeout_seconds = 60
    timeout_submission = {'bid': cu(0)}

    def vars_for_template(self):
        valuation = self._ensure_valuation()
        s_no, r_in_s = phase_and_round_in_session(self.round_number)
        return dict(
            valuation=valuation,
            session_no=s_no,
            round_in_session=r_in_s,
            ROUNDS_PER_SESSION=10,
        )

class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs

class Results(BasePage):
    def vars_for_template(self):
        # (Usually valuation is already set by Bid page, but keep it safe)
        valuation = self._ensure_valuation()
        opp = self.player.get_others_in_group()[0]
        you_won = (self.group.winner_id_in_group == self.player.id_in_group)
        s_no, r_in_s = phase_and_round_in_session(self.round_number)
        return dict(
            your_bid=self.player.bid,
            opp_bid=opp.bid,
            valuation=valuation,
            price=self.group.price,
            you_won=you_won,
            session_no=s_no,
            round_in_session=r_in_s,
            ROUNDS_PER_SESSION=10,
        )

page_sequence = [Instructions, Bid, ResultsWaitPage, Results]


