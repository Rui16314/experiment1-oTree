# experiment1/pages.py
from otree.api import *
import json

from .models import (
    C, Subsession, Group, Player,
    phase_and_round_in_session, rules_for_round, set_payoffs
)


# ---------- Common mixin to expose round/session info ----------

class RoundInfo:
    def vars_for_template(self):
        s_no, r_in_s = phase_and_round_in_session(self.round_number)
        ctx = dict(
            session_no=s_no,
            round_in_session=r_in_s,
            ROUNDS_PER_SESSION=C.ROUNDS_PER_SESSION,
        )
        # add valuation where available (safe if present)
        if hasattr(self, 'player') and self.player.valuation is not None:
            ctx['valuation'] = self.player.valuation
        # human-readable price rule
        ctx['price_rule'] = 'first-price' if rules_for_round(self.round_number)['price'] == 'first' else 'second-price'
        return ctx


# ---------- Chat (live) support ----------

def live_chat(player: Player, data):
    """data expected as {'text': '...'}"""
    g: Group = player.group
    try:
        arr = json.loads(g.chat_history)
    except Exception:
        arr = []
    msg = dict(pid=player.id_in_group, text=(data or {}).get('text', ''))
    if msg['text'].strip():
        arr.append(msg)
        g.chat_history = json.dumps(arr)
    # broadcast updated history to both players
    return {p.id_in_group: arr for p in g.get_players()}


# ---------- Pages ----------

class Instructions(RoundInfo, Page):
    def is_displayed(self):
        # only first round of each 10-round session
        _, ris = phase_and_round_in_session(self.round_number)
        return ris == 1


class Chat(RoundInfo, Page):
    live_method = live_chat

    def is_displayed(self):
        return rules_for_round(self.round_number)['chat']

    @staticmethod
    def js_vars(player: Player):
        return dict(my_id=player.id_in_group)


class Bid(RoundInfo, Page):
    form_model = 'player'
    form_fields = ['bid']

    # 60-second timer
    timeout_seconds = 60

    def is_displayed(self):
        # bidding every round
        return True


class WaitForBoth(WaitPage):
    after_all_players_arrive = set_payoffs


class Results(RoundInfo, Page):
    pass


page_sequence = [Instructions, Chat, Bid, WaitForBoth, Results]

