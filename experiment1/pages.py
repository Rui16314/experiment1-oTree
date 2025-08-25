# experiment1/pages.py
from otree.api import *
from .models import C, Player, Group, Subsession, set_payoffs, session_and_round, rules_for_round


def price_label(rn: int) -> str:
    return 'first-price' if rules_for_round(rn)['price'] == 'first' else 'second-price'


class Instructions(Page):
    """Show once at the start of each 10-round session."""
    def is_displayed(self):
        _, r = session_and_round(self.round_number)
        return r == 1

    def vars_for_template(self):
        s, r = session_and_round(self.round_number)
        rules = rules_for_round(self.round_number)
        return dict(
            session_no=s,
            round_in_session=r,
            ROUNDS_PER_SESSION=C.ROUNDS_PER_SESSION,
            price_rule=price_label(self.round_number),
            matching=rules['matching'],
            chat=rules['chat'],
        )


class Chat(LivePage):
    """Simple real-time chat for sessions 3 & 6."""
    def is_displayed(self):
        return rules_for_round(self.round_number)['chat']

    def vars_for_template(self):
        s, r = session_and_round(self.round_number)
        return dict(session_no=s, round_in_session=r)

    @staticmethod
    def live_method(player: Player, data):
        txt = (data or {}).get('text', '').strip()
        if not txt:
            return
        msg = f"P{player.id_in_group}: {txt}"
        # Broadcast to everyone in the group (0 targets all)
        return {0: dict(messages=[msg])}


class Bid(Page):
    form_model = 'player'
    form_fields = ['bid']
    timeout_seconds = 60

    def vars_for_template(self):
        s, r = session_and_round(self.round_number)
        return dict(
            session_no=s,
            round_in_session=r,
            ROUNDS_PER_SESSION=C.ROUNDS_PER_SESSION,
            valuation=self.player.valuation,
        )

    def before_next_page(self):
        # If the participant times out, convert to the session's auto-bid.
        if self.player.bid is None:
            first_price = (rules_for_round(self.round_number)['price'] == 'first')
            self.player.auto_bid_used = True
            self.player.bid = (self.player.valuation / 2) if first_price else self.player.valuation


class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs


class Results(Page):
    def vars_for_template(self):
        s, r = session_and_round(self.round_number)
        opp = self.player.get_others_in_group()[0]
        you_won = (self.group.winner_id_in_group == self.player.id_in_group)
        return dict(
            session_no=s,
            round_in_session=r,
            your_bid=self.player.bid,
            opp_bid=opp.bid,
            valuation=self.player.valuation,
            opp_valuation=opp.valuation,
            price=self.group.price,
            you_won=you_won,
        )


page_sequence = [Instructions, Chat, Bid, ResultsWaitPage, Results]


