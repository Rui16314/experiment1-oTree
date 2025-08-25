# experiment1/pages.py
from otree.api import *
from .models import C, set_payoffs, session_and_round_in_session, rules_for_round
from .models import ChatMessage, chat_history_for   # NEW
import time                                         # NEW


def _session_and_round(rn: int):
    return session_and_round_in_session(rn)


class Instructions(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number in (1, 11, 21, 31, 41, 51)

    @staticmethod
    def vars_for_template(player: Player):
        s_no, r_in_s = _session_and_round(player.round_number)
        return dict(session_no=s_no, round_in_session=r_in_s)


class ChatBid(Page):  # NEW
    """Bid page WITH live chat — shows only in Sessions 3 & 6."""
    form_model = 'player'
    form_fields = ['bid']
    timeout_seconds = 60
    live_method = 'live_chat'

    @staticmethod
    def is_displayed(player: Player):
        return rules_for_round(player.round_number)['chat']  # True in sessions 3 & 6

    @staticmethod
    def vars_for_template(player: Player):
        s_no, r_in_s = _session_and_round(player.round_number)
        return dict(
            session_no=s_no,
            round_in_session=r_in_s,
            valuation=player.valuation,
            my_id=player.id_in_group,
        )

    # live handler for chat
    def live_chat(self, data):
        kind = data.get('type')
        if kind == 'join':
            # send existing history only to the joiner
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
                ts=time.time(),  # timestamp here -> needs import time
            )
            # broadcast to both players on the page
            return {0: {'kind': 'message', 'sid': self.player.id_in_group, 'text': text}}


class Bid(Page):
    """Bid page WITHOUT chat — shows in sessions 1,2,4,5."""
    form_model = 'player'
    form_fields = ['bid']
    timeout_seconds = 60

    @staticmethod
    def is_displayed(player: Player):
        return not rules_for_round(player.round_number)['chat']

    @staticmethod
    def vars_for_template(player: Player):
        s_no, r_in_s = _session_and_round(player.round_number)
        return dict(
            session_no=s_no,
            round_in_session=r_in_s,
            valuation=player.valuation
        )


class ComputeResults(WaitPage):
    after_all_players_arrive = set_payoffs


class Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        s_no, r_in_s = _session_and_round(player.round_number)
        opp = player.get_others_in_group()[0]
        g = player.group
        you_won = (g.winner_id_in_group == player.id_in_group)
        return dict(
            session_no=s_no,
            round_in_session=r_in_s,
            your_bid=player.bid if player.bid is not None else cu(0),
            opp_bid=opp.bid if opp.bid is not None else cu(0),
            price=g.price,
            valuation=player.valuation,
            you_won=you_won,
        )


page_sequence = [Instructions, ChatBid, Bid, ComputeResults, Results]


