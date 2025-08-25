from otree.api import *
from .models import C, set_payoffs, rules_for_round, phase_and_round_in_session
import time


class Instructions(Page):
    # show only at the start of each 10-round session
    def is_displayed(self):
        _, r_in_s = phase_and_round_in_session(self.round_number)
        return r_in_s == 1

    def vars_for_template(self):
        s_no, r_in_s = phase_and_round_in_session(self.round_number)
        r = rules_for_round(self.round_number)
        return dict(
            ROUNDS_PER_SESSION=C.ROUNDS_PER_SESSION,
            session_no=s_no,
            round_in_session=r_in_s,
            price_rule=r['price'],               # 'first' or 'second'
            matching=r['matching'],              # 'random' or 'fixed'
            chat=r['chat'],                      # True/False
        )

 class ChatBid(Page):  # ADD
    """
    Bid page with live chat. Shown only when the session has chat enabled (Sessions 3 & 6).
    """
    form_model = 'player'
    form_fields = ['bid']
    timeout_seconds = 60
    live_method = 'live_chat'

    def is_displayed(self):
        return rules_for_round(self.round_number)['chat']

    # Defensive: ensure valuation is there (should already be set in creating_session)
    def _ensure_valuation(self):
        if self.player.field_maybe_none('valuation') is None:
            from .models import draw_valuation
            self.player.valuation = draw_valuation()

    def vars_for_template(self):
        self._ensure_valuation()
        s_no, r_in_s = phase_and_round_in_session(self.round_number)
        return dict(
            ROUNDS_PER_SESSION=C.ROUNDS_PER_SESSION,
            session_no=s_no,
            round_in_session=r_in_s,
            valuation=self.player.valuation,
            my_id=self.player.id_in_group,
        )

    # Live handler for chat
    def live_chat(self, data):
        kind = data.get('type')

        if kind == 'join':
            # send full history just to the joiner
            return {
                self.id_in_group: {
                    'kind': 'history',
                    'items': chat_history_for(self.group),
                }
            }

        if kind == 'msg':
            text = (data.get('text') or '').strip()
            if not text:
                return
            ChatMessage.create(
                group=self.group,
                sender_id_in_group=self.player.id_in_group,
                text=text,
                ts=time.time(),
            )
            # broadcast to both players on this page (key 0 = group broadcast)
            return {
                0: {
                    'kind': 'message',
                    'sid': self.player.id_in_group,
                    'text': text,
                }
            }


class Bid(Page):
    # unchanged; only show when chat is NOT enabled
    form_model = 'player'
    form_fields = ['bid']
    timeout_seconds = 60

    def is_displayed(self):
        return not rules_for_round(self.round_number)['chat']

    def _ensure_valuation(self):
        if self.player.field_maybe_none('valuation') is None:
            from .models import draw_valuation
            self.player.valuation = draw_valuation()

    def vars_for_template(self):
        self._ensure_valuation()
        s_no, r_in_s = phase_and_round_in_session(self.round_number)
        return dict(
            ROUNDS_PER_SESSION=C.ROUNDS_PER_SESSION,
            session_no=s_no,
            round_in_session=r_in_s,
            valuation=self.player.valuation,
        )


class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs


class Results(Page):
    def vars_for_template(self):
        s_no, r_in_s = phase_and_round_in_session(self.round_number)
        opp = self.player.get_others_in_group()[0]
        you_won = (self.group.winner_id_in_group == self.player.id_in_group)
        return dict(
            ROUNDS_PER_SESSION=C.ROUNDS_PER_SESSION,
            session_no=s_no,
            round_in_session=r_in_s,
            your_bid=self.player.bid,
            opp_bid=opp.bid,
            valuation=self.player.valuation,
            price=self.group.price,
            you_won=you_won,
        )


# IMPORTANT: include ChatBid in the sequence; it will only render in chat sessions.
page_sequence = [Instructions, ChatBid, Bid, ResultsWaitPage, Results]




