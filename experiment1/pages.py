# experiment1/pages.py
from otree.api import *
from .models import (
    C, Player, Group, Subsession,
    rules_for_round, session_and_round, set_payoffs, draw_valuation
)


def price_label_for_round(rn: int) -> str:
    return 'first-price' if rules_for_round(rn)['price'] == 'first' else 'second-price'


class Instructions(Page):
    def vars_for_template(self):
        s_no, r_in_s = session_and_round(self.round_number)
        r = rules_for_round(self.round_number)
        return dict(
            ROUNDS_PER_SESSION=C.ROUNDS_PER_SESSION,
            session_no=s_no,
            round_in_session=r_in_s,
            price_rule=price_label_for_round(self.round_number),
            matching=r['matching'],
            chat=r['chat'],
        )


class Bid(Page):
    form_model = 'player'
    form_fields = ['bid']
    timeout_seconds = 60
    timeout_submission = {'bid': cu(0)}

    def vars_for_template(self):
        # SAFELY read possibly-null value without raising, and ensure it's set
        val = self.player.field_maybe_none('valuation')
        if val is None:
            self.player.valuation = draw_valuation()
            val = self.player.valuation

        s_no, r_in_s = session_and_round(self.round_number)
        return dict(
            valuation=val,
            ROUNDS_PER_SESSION=C.ROUNDS_PER_SESSION,
            session_no=s_no,
            round_in_session=r_in_s,
        )


class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs


class Results(Page):
    def vars_for_template(self):
        s_no, r_in_s = session_and_round(self.round_number)
        others = self.player.get_others_in_group()
        opp = others[0] if others else None
        you_won = (self.group.winner_id_in_group == self.player.id_in_group)
        return dict(
            your_bid=self.player.bid,
            opp_bid=opp.bid if opp else None,
            valuation=self.player.valuation,
            price=self.group.price,
            you_won=you_won,
            ROUNDS_PER_SESSION=C.ROUNDS_PER_SESSION,
            session_no=s_no,
            round_in_session=r_in_s,
        )


page_sequence = [Instructions, Bid, ResultsWaitPage, Results]


