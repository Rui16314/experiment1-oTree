# experiment1/pages.py
from otree.api import *
from .models import C, Subsession, Group, Player, set_payoffs


class Instructions(Page):
    """Shown once at the start; exposes session config to the template."""
    def is_displayed(self):
        return self.round_number == 1

    def vars_for_template(self):
        cfg = self.session.config
        return dict(
            price_rule=cfg.get('price_rule', getattr(C, 'PRICE_RULE', 'first')),
            matching=cfg.get('matching', getattr(C, 'MATCHING', 'random')),
            tie_rule=cfg.get('tie_rule', getattr(C, 'TIE_RULE', 'random')),
            chat=bool(cfg.get('chat', False)),
            num_rounds=C.NUM_ROUNDS,
            # safe access; returns None if not yet set (does not raise)
            valuation=self.player.field_maybe_none('valuation'),
        )


class Bid(Page):
    """Players submit a bid; we just return the field list (no peeking at
    valuation here, to avoid 'None' access errors)."""
    form_model = 'player'
    form_fields = ['bid']
    timeout_seconds = 60  # optional; change as you like

    def vars_for_template(self):
        # Use safe accessor in templates just in case
        return dict(valuation=self.player.field_maybe_none('valuation'))


class ResultsWaitPage(WaitPage):
    """Compute winner/price/payoffs after both bids are in."""
    after_all_players_arrive = set_payoffs


class Results(Page):
    """Show round outcome."""
    def vars_for_template(self):
        g = self.group
        me = self.player
        opp = me.get_others_in_group()[0]
        winner_id = g.winner_id_in_group
        return dict(
            you_won = (me.id_in_group == winner_id),
            price   = g.price,
            your_bid= me.bid,
            opp_bid = opp.bid,
            your_val= me.field_maybe_none('valuation'),
        )


page_sequence = [Instructions, Bid, ResultsWaitPage, Results]

