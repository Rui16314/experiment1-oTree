# experiment1/pages.py
from otree.api import *
from .models import C, set_payoffs, draw_valuation

class Instructions(Page):
    def vars_for_template(self):
        # For now you hard-code these (or read from session.config)
        price_rule = 'first-price'   # 'first-price' or 'second-price'
        matching   = 'random'        # 'random' or 'fixed'
        chat       = False

        # choose the partial to include
        if price_rule == 'first-price':
            if matching == 'random' and not chat:
                tmpl = "experiment1/Instructions_S1_First.html"
            elif matching == 'fixed' and not chat:
                tmpl = "experiment1/Instructions_S2_FirstRepeated.html"
            elif matching == 'fixed' and chat:
                tmpl = "experiment1/Instructions_S3_FirstRepeated_Chat.html"
            else:
                tmpl = "experiment1/Instructions_S1_First.html"
        else:
            if matching == 'random' and not chat:
                tmpl = "experiment1/Instructions_S4_Second.html"
            elif matching == 'fixed' and not chat:
                tmpl = "experiment1/Instructions_S5_SecondRepeated.html"
            elif matching == 'fixed' and chat:
                tmpl = "experiment1/Instructions_S6_SecondRepeated_Chat.html"
            else:
                tmpl = "experiment1/Instructions_S4_Second.html"

        return dict(
            price_rule=price_rule,
            matching=matching,
            chat=chat,
            ROUNDS=C.NUM_ROUNDS,
            instruction_tmpl=tmpl,
        )


class Bid(Page):
    form_model = 'player'
    form_fields = ['bid']
    timeout_seconds = 60
    timeout_submission = {'bid': cu(0)}

    def vars_for_template(self):
        # SAFE read that doesn't crash if the field is None
        val = self.player.field_maybe_none('valuation')
        if val is None:
            # defensive fallback in case creating_session didn't run
            val = draw_valuation()
            self.player.valuation = val
        return dict(valuation=val)


class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs


class Results(Page):
    def vars_for_template(self):
        opp = self.player.get_others_in_group()[0]
        you_won = (self.group.winner_id_in_group == self.player.id_in_group)
        return dict(
            your_bid=self.player.bid,
            opp_bid=opp.bid,
            valuation=self.player.valuation,
            price=self.group.price,
            you_won=you_won,
        )


page_sequence = [Instructions, Bid, ResultsWaitPage, Results]


