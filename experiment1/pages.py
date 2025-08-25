# experiment1/pages.py
from otree.api import *
from .models import C, Subsession, Group, Player, set_payoffs, draw_valuation, rules_for_round, phase_and_round_in_session

def price_label_for_round(rn: int) -> str:
    return 'first-price' if rules_for_round(rn)['price'] == 'first' else 'second-price'

class Instructions(Page):
    def vars_for_template(self):
        s_no, r_in_s = phase_and_round_in_session(self.round_number)
        r = rules_for_round(self.round_number)
        return dict(
            ROUNDS_PER_SESSION=C.ROUNDS_PER_SESSION,   # <-- add
            ROUNDS=C.ROUNDS_PER_SESSION,               # keep for older templates
            session_no=s_no,
            round_in_session=r_in_s,
            price_rule=price_label_for_round(self.round_number),
            matching=r['matching'],
            tie_rule='random',
            chat=r['chat'],
        )

class Bid(Page):
    form_model = 'player'
    form_fields = ['bid']
    timeout_seconds = 60
    timeout_submission = {'bid': cu(0)}

    def _ensure_valuation(self):
        if self.player.field_maybe_none('valuation') is None:
            self.player.valuation = draw_valuation()
        return self.player.valuation

    def vars_for_template(self):
        s_no, r_in_s = phase_and_round_in_session(self.round_number)
        return dict(
            ROUNDS_PER_SESSION=C.ROUNDS_PER_SESSION,   # <-- add
            ROUNDS=C.ROUNDS_PER_SESSION,
            session_no=s_no,
            round_in_session=r_in_s,
            valuation=self._ensure_valuation(),
        )

class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs

class Results(Page):
    def vars_for_template(self):
        s_no, r_in_s = phase_and_round_in_session(self.round_number)
        opp = self.player.get_others_in_group()[0]
        you_won = (self.group.winner_id_in_group == self.player.id_in_group)
        return dict(
            ROUNDS_PER_SESSION=C.ROUNDS_PER_SESSION,   # <-- add
            ROUNDS=C.ROUNDS_PER_SESSION,
            session_no=s_no,
            round_in_session=r_in_s,
            your_bid=self.player.bid,
            opp_bid=opp.bid,
            valuation=self.player.valuation,
            price=self.group.price,
            you_won=you_won,
        )

page_sequence = [Instructions, Bid, ResultsWaitPage, Results]


