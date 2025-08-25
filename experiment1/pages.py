# experiment1/pages.py
from otree.api import *
from .models import (
    C, Player, Group, Subsession,
    draw_valuation, set_payoffs,
    phase_and_round_in_session, rules_for_round
)

ROUNDS_PER_SESSION = 10
BID_TIMEOUT_SECONDS = 60


def _price_label_for_round(rn: int) -> str:
    """Return the label your templates check: 'first-price' or 'second-price'."""
    return 'first-price' if rules_for_round(rn)['price'] == 'first' else 'second-price'


def _fmt_mmss(seconds: int) -> str:
    m = seconds // 60
    s = seconds % 60
    return f"{m}:{s:02d}"


class _CommonPage(Page):
    """Mix-in with helpers & common context."""
    def _ensure_valuation(self):
        """
        Make sure valuation exists before any template accesses it.
        Accessing a null CurrencyField raises in oTree, so we catch and set.
        """
        try:
            _ = self.player.valuation  # triggers TypeError if still null
        except TypeError:
            self.player.valuation = draw_valuation()

    def _common_context(self) -> dict:
        s_no, r_in_s = phase_and_round_in_session(self.round_number)
        r = rules_for_round(self.round_number)
        return dict(
            # session/round info for headers
            session_no=s_no,                    # 1..6
            round_in_session=r_in_s,            # 1..10
            ROUNDS_PER_SESSION=ROUNDS_PER_SESSION,

            # rule switches for your instruction partials
            price_rule=_price_label_for_round(self.round_number),   # 'first-price' / 'second-price'
            matching=r['matching'],            # 'random' or 'fixed'
            chat=r['chat'],                    # True in sessions 3 & 6
            tie_rule='random',                 # as specified
        )


class Instructions(_CommonPage):
    """Show once at the beginning of each 10-round session."""
    def is_displayed(self):
        _, r_in_s = phase_and_round_in_session(self.round_number)
        return r_in_s == 1

    def vars_for_template(self):
        ctx = self._common_context()
        # also expose total rounds (60) if any template uses it
        ctx.update(ROUNDS=C.NUM_ROUNDS)
        return ctx


class Bid(_CommonPage):
    form_model = 'player'
    form_fields = ['bid']
    timeout_seconds = BID_TIMEOUT_SECONDS
    timeout_submission = {'bid': cu(0)}

    def vars_for_template(self):
        # safety: never let valuation be null when template renders
        self._ensure_valuation()
        ctx = self._common_context()
        ctx.update(
            valuation=self.player.valuation,
            timeout_seconds_display=_fmt_mmss(self.timeout_seconds or BID_TIMEOUT_SECONDS),
        )
        return ctx


class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs


class Results(_CommonPage):
    def vars_for_template(self):
        ctx = self._common_context()

        others = self.player.get_others_in_group()
        opp = others[0] if others else None

        you_won = (self.group.winner_id_in_group == self.player.id_in_group)
        ctx.update(
            your_bid=self.player.bid,
            opp_bid=(opp.bid if opp else cu(0)),
            valuation=self.player.valuation,
            price=self.group.price,
            you_won=you_won,
        )
        return ctx


page_sequence = [Instructions, Bid, ResultsWaitPage, Results]



