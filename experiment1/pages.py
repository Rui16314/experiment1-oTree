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
            price_rule=rules['price_rule'],
            matching=rules['matching'],
            chat=rules['chat'],
        )


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
            # Note: The instructions specify v/2 or v for bots, but this handles human timeouts.
            self.player.bid = cu(0)


class ResultsWaitPage(WaitPage):
    title_text = "Please wait"
    body_text = "Waiting for the other participant."
    after_all_players_arrive = set_group_payoffs



# ... (existing classes like Instructions, Bid, ResultsWaitPage, Results) ...

class SessionSummary(Page):
    def is_displayed(self):
        s_no, r_in_s = session_no_and_round_in_session(self.round_number)
        return r_in_s == C.ROUNDS_PER_SESSION and s_no < 6

    def vars_for_template(self):
        # ... (logic to generate data for single session summary) ...
        pass


class FinalResults(Page):
    def is_displayed(self):
        return self.round_number == C.NUM_ROUNDS

    def vars_for_template(self):
        # Data aggregation from all sessions
        all_players = self.subsession.in_rounds(1, C.NUM_ROUNDS).get_players()
        all_sessions_bids = []
        all_session_revenues_by_round = []
        all_session_revenues = []

        for s_no in range(1, 7):
            session_players = [p for p in all_players if session_no_and_round_in_session(p.round_number)[0] == s_no]
            session_groups = [g for g in self.subsession.in_rounds(1, C.NUM_ROUNDS).get_groups() if session_no_and_round_in_session(g.round_number)[0] == s_no]
            
            # 1) Average Bidding Behavior
            valuations = [p.valuation for p in session_players]
            bids = [p.bid for p in session_players]
            
            bins = [[] for _ in range(11)]
            for v, b in zip(valuations, bids):
                if b is not None:
                    bin_index = min(int(v // 10), 9)
                    bins[bin_index].append(b)

            avg_bids = [sum(b) / len(b) if b else None for b in bins]
            
            rules = rules_for_round((s_no - 1) * C.ROUNDS_PER_SESSION + 1)
            all_sessions_bids.append({
                'session_no': s_no,
                'price_rule': rules['price_rule'],
                'matching': rules['matching'],
                'chat': rules['chat'],
                'data': avg_bids
            })

            # 2) Average revenue by round
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
            
            # 3) Overall Average Revenue
            all_revenues = [g.price for g in session_groups]
            avg_revenue = sum(all_revenues) / len(all_revenues) if all_revenues else 0
            all_session_revenues.append({
                'session_no': s_no,
                'price_rule': rules['price_rule'],
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
