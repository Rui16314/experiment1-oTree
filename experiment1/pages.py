# experiment1/pages.py
from otree.api import *
from .models import C, rules_for_round, session_no_and_round_in_session, set_group_payoffs

INSTRUCTION_TEMPLATES = {
    1: 'experiment1/Instructions_S1_First.html',
    2: 'experiment1/Instructions_S2_FirstRepeated.html',
    3: 'experiment1/Instructions_S3_FirstRepeated_Chat.html',
    4: 'experiment1/Instructions_S4_Second.html',
    5: 'experiment1/Instructions_S5_SecondRepeated.html',
    6: 'experiment1/Instructions_S6_SecondRepeated_Chat.html',
}

# Add the missing RoundInfo class
class RoundInfo:
    def vars_for_template(self):
        s_no, r_in_s = session_no_and_round_in_session(self.round_number)
        rules = rules_for_round(self.round_number)
        return {
            'session_no': s_no,
            'round_in_session': r_in_s,
            'ROUNDS_PER_SESSION': C.ROUNDS_PER_SESSION,
            'rules': rules
        }

class Instructions(RoundInfo, Page):
    def is_displayed(self):
        # only first round of each 10-round session
        s_no, r_in_s = session_no_and_round_in_session(self.round_number)
        return r_in_s == 1

    def vars_for_template(self):
        ctx = super().vars_for_template()
        s_no = ctx['session_no']
        # Map session -> partial file to include
        partial_map = {
            1: 'experiment1/instructions/Instructions_S1_First.html',
            2: 'experiment1/instructions/Instructions_S2_FirstRepeated.html',
            3: 'experiment1/instructions/Instructions_S3_FirstRepeated_Chat.html',
            4: 'experiment1/instructions/Instructions_S4_Second.html',
            5: 'experiment1/instructions/Instructions_S5_SecondRepeated.html',
            6: 'experiment1/instructions/Instructions_S6_SecondRepeated_Chat.html',
        }
        ctx['session_partial'] = partial_map[s_no]
        # Show "General Instructions" only before Session 1
        ctx['show_general'] = (s_no == 1)
        return ctx

class Bid(Page):
    form_model = 'player'
    form_fields = ['bid']
    timeout_seconds = 60

    def live_method(self, data):
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

class SessionSummary(Page):
    def is_displayed(self):
        s_no, r_in_s = session_no_and_round_in_session(self.round_number)
        return r_in_s == C.ROUNDS_PER_SESSION and s_no < 6

    def vars_for_template(self):
        pass

class FinalResults(Page):
    def is_displayed(self):
        return self.round_number == C.NUM_ROUNDS

    def vars_for_template(self):
        all_players = self.session.get_players()
        all_groups = self.session.get_groups()
        all_sessions_bids = []
        all_session_revenues_by_round = []
        all_session_revenues = []

        for s_no in range(1, 7):
            session_players = [p for p in all_players if session_no_and_round_in_session(p.round_number)[0] == s_no]
            session_groups = [g for g in all_groups if session_no_and_round_in_session(g.round_number)[0] == s_no]
            valuations = [p.valuation for p in session_players]
            bids = [p.bid for p in session_players]
            bins = [[] for _ in range(10)]
            for v, b in zip(valuations, bids):
                if b is not None:
                    bin_index = min(int(v // 10), 9)
                    bins[bin_index].append(b)
            avg_bids = [sum(b) / len(b) if len(b) > 0 else None for b in bins]
            rules = rules_for_round((s_no - 1) * C.ROUNDS_PER_SESSION + 1)
            all_sessions_bids.append({
                'session_no': s_no,
                'price_rule': rules['price'],
                'matching': rules['matching'],
                'chat': rules['chat'],
                'data': avg_bids
            })
            revenues_by_round = []
            for r_in_s in range(1, 11):
                round_groups = [g for g in session_groups if session_no_and_round_in_session(g.round_number)[1] == r_in_s]
                revenues = [g.price for g in round_groups]
                if revenues:
                    revenues_by_round.append(sum(revenues) / len(revenues))
                else:
                    revenues_by_round.append(None)
            all_session_revenues_by_round.append({
                'session_no': s_no,
                'data': revenues_by_round
            })
            all_revenues = [g.price for g in session_groups]
            avg_revenue = sum(all_revenues) / len(all_revenues) if len(all_revenues) > 0 else 0
            all_session_revenues.append({
                'session_no': s_no,
                'price_rule': rules['price'],
                'matching': rules['matching'],
                'chat': rules['chat'],
                'avg_revenue': avg_revenue
            })
        return dict(
            all_session_bids=all_sessions_bids,
            all_session_revenues_by_round=all_session_revenues_by_round,
            all_session_revenues=all_session_revenues
        )

page_sequence = [Instructions, Bid, ResultsWaitPage, Results, SessionSummary, FinalResults]
