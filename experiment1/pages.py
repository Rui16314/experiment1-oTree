# experiment1/pages.py
from otree.api import *
from .models import C, rules_for_round, session_no_and_round_in_session, set_group_payoffs


class Instructions(Page):
    """Shown only once at the beginning of each 10-round session."""
    def is_displayed(self):
        _, r_in_s = session_no_and_round_in_session(self.round_number)
        return r_in_s == 1

    def vars_for_template(self):
        s_no, r_in_s = session_no_and_round_in_session(self.round_number)
        rules = rules_for_round(self.round_number)
        return dict(
            session_no=s_no,
            round_in_session=r_in_s,
            ROUNDS_PER_SESSION=C.ROUNDS_PER_SESSION,
            price_rule=rules['price_rule'],       # 'first' / 'second'
            matching=rules['matching'],           # 'random' / 'fixed'
            chat=rules['chat'],                   # True/False
        )


class Bid(Page):
    form_model = 'player'
    form_fields = ['bid']
    timeout_seconds = 60  # shows the yellow oTree timer box automatically

    # simple live chat, enabled only on chat sessions (3 and 6)
    def live_method(self, data):
        # data is a dict sent from JS; broadcast to both players
        text = (data or {}).get('text', '').strip()
        if not text:
            return
        return {0: dict(sender=self.player.id_in_group, text=text)}

    def vars_for_template(self):
        s_no, r_in_s = session_no_and_round_in_session(self.round_number)
        rules = rules_for_round(self.round_number)
        return dict(
            session_no=s_no,
            round_in_session=r_in_s,
            ROUNDS_PER_SESSION=C.ROUNDS_PER_SESSION,
            valuation=self.player.valuation,
            chat_enabled=rules['chat'],
        )

    def before_next_page(self, timeout_happened):
        # if participant runs out of time, set bid to 0 so payoff code never sees None
        if timeout_happened and self.player.bid is None:
            self.player.bid = cu(0)


class ResultsWaitPage(WaitPage):
    title_text = "Please wait"
    body_text = "Waiting for the other participant."

    after_all_players_arrive = set_group_payoffs


class Results(Page):
    def vars_for_template(self):
        s_no, r_in_s = session_no_and_round_in_session(self.round_number)
        other = self.player.get_others_in_group()[0]
        you_won = self.group.winner_id_in_group == self.player.id_in_group
        return dict(
            session_no=s_no,
            round_in_session=r_in_s,
            ROUNDS_PER_SESSION=C.ROUNDS_PER_SESSION,
            your_bid=self.player.bid,
            opp_bid=other.bid,
            valuation=self.player.valuation,
            price=self.group.price,
            you_won=you_won,
        )


page_sequence = [Instructions, Bid, ResultsWaitPage, Results]


