# experiment1/pages.py
from otree.api import *
from .models import (
    C,
    rules_for_round,
    phase_and_round_in_session,
    set_payoffs,
    draw_valuation,
)

def price_label_for_round(rn: int) -> str:
    """Return the label expected by your templates: 'first-price' / 'second-price'."""
    return 'second-price' if rules_for_round(rn)['price'] == 'second' else 'first-price'


class Instructions(Page):
    def vars_for_template(self):
        s_no, r_in_s = phase_and_round_in_session(self.round_number)
        r = rules_for_round(self.round_number)
        return dict(
            # used by session partials
            ROUNDS_PER_SESSION=10,
            session_no=s_no,                  # 1..6
            round_in_session=r_in_s,          # 1..10
            price_rule=price_label_for_round(self.round_number),
            matching=r['matching'],           # 'random' or 'fixed'
            tie_rule='random',
            chat=r['chat'],                   # True / False
        )


class Bid(Page):
    form_model = 'player'
    form_fields = ['bid']
    timeout_seconds = 60
    timeout_submission = {'bid': cu(0)}  # cu imported via otree.api *

    def _ensure_valuation(self):
        # guard in case a valuation is missing for this player/round
        if self.player.valuation is None:
            self.player.valuation = draw_valuation()
        return self.player.valuation

    def vars_for_template(self):
        s_no, r_in_s = phase_and_round_in_session(self.round_number)
        return dict(
            valuation=self._ensure_valuation(),
            session_no=s_no,
            round_in_session=r_in_s,
            ROUNDS_PER_SESSION=10,
        )


class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs   # function imported from models.py


class Results(Page):
    def vars_for_template(self):
        opp = self.player.get_others_in_group()[0]
        you_won = (self.group.winner_id_in_group == self.player.id_in_group)
        s_no, r_in_s = phase_and_round_in_session(self.round_number)
        return dict(
            your_bid=self.player.bid,
            opp_bid=opp.bid,
            valuation=self.player.valuation,
            price=self.group.price,
            you_won=you_won,
            session_no=s_no,
            round_in_session=r_in_s,
            ROUNDS_PER_SESSION=10,
        )


page_sequence = [Instructions, Bid, ResultsWaitPage, Results]

