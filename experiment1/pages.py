# experiment1/pages.py
from otree.api import *
from .models import C, Player, Group, Subsession, set_payoffs, draw_valuation

ROUNDS_PER_SESSION = 10


def common_ctx(player: Player):
    r = player.round_number
    return dict(
        ROUNDS=ROUNDS_PER_SESSION,
        session_num=((r - 1) // ROUNDS_PER_SESSION) + 1,
        round_in_session=((r - 1) % ROUNDS_PER_SESSION) + 1,
    )


class Instructions(Page):
    def vars_for_template(self):
        ctx = common_ctx(self.player)
        ctx.update(
            dict(
                price_rule="first-price",
                matching="random",
                tie_rule="random",
                chat=False,
            )
        )
        return ctx


class Bid(Page):
    form_model = "player"
    form_fields = ["bid"]
    timeout_seconds = 60
    timeout_submission = {"bid": cu(0)}

    def vars_for_template(self):
        p = self.player
        # SAFE check: don't read a null field directly
        if p.field_maybe_none("valuation") is None:
            p.valuation = draw_valuation()

        ctx = common_ctx(p)
        ctx.update(dict(valuation=p.valuation))
        return ctx


class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs


class Results(Page):
    def vars_for_template(self):
        p = self.player
        ctx = common_ctx(p)
        opp = p.get_others_in_group()[0]
        you_won = (self.group.winner_id_in_group == p.id_in_group)
        ctx.update(
            dict(
                your_bid=p.bid,
                opp_bid=opp.bid,
                valuation=p.valuation,
                price=self.group.price,
                you_won=you_won,
            )
        )
        return ctx


page_sequence = [Instructions, Bid, ResultsWaitPage, Results]
