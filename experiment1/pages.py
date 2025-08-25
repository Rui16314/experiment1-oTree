# experiment1/pages.py
from otree.api import *
from .models import C, Player, Group, Subsession, set_payoffs, rules_for_round, session_no_and_round_in_session


def price_label(round_number: int):
    return 'first-price' if rules_for_round(round_number)['price'] == 'first' else 'second-price'


class Instructions(Page):
    def vars_for_template(self):
        s_no, r_in = session_no_and_round_in_session(self.round_number)
        rules = rules_for_round(self.round_number)
        return dict(
            session_no=s_no,
            round_in_session=r_in,
            ROUNDS_PER_SESSION=C.ROUNDS_PER_SESSION,
            price_rule=price_label(self.round_number),
            matching=rules['matching'],
            chat=rules['chat'],
        )


class ChatIntro(Page):
    """Placeholder page shown only in chat sessions.
    If you add a real chat app later, replace this page with that app.
    """
    def is_displayed(self):
        return rules_for_round(self.round_number)['chat']


class Bid(Page):
    form_model = 'player'
    form_fields = ['bid']
    timeout_seconds = 60

    def vars_for_template(self):
        s_no, r_in = session_no_and_round_in_session(self.round_number)
        return dict(
            session_no=s_no,
            round_in_session=r_in,
            ROUNDS_PER_SESSION=C.ROUNDS_PER_SESSION,
            valuation=self.player.valuation,
        )

    def before_next_page(self):
        # If the player times out: system sets bid = v/2 and marks timed_out
        if self.timeout_happened:
            self.player.bid = (self.player.valuation / 2)
            self.player.timed_out = True


class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs


class Results(Page):
    def vars_for_template(self):
        s_no, r_in = session_no_and_round_in_session(self.round_number)
        opp = self.player.get_others_in_group()[0]
        you_won = (self.group.winner_id_in_group == self.player.id_in_group)
        return dict(
            session_no=s_no,
            round_in_session=r_in,
            ROUNDS_PER_SESSION=C.ROUNDS_PER_SESSION,
            your_bid=self.player.bid,
            opp_bid=opp.bid,
            valuation=self.player.valuation,
            price=self.group.price,
            you_won=you_won,
        )


def chat_first(round_number: int):
    """True for sessions 3 and 6 (chat sessions)."""
    r = rules_for_round(round_number)
    return r['chat']


# Page order:
#   Instructions  -> (ChatIntro if chat) -> Bid -> ResultsWaitPage -> Results
page_sequence = [Instructions, ChatIntro, Bid, ResultsWaitPage, Results]



