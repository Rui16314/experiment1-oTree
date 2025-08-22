from otree.api import *
from .models import C, Player, Group, Subsession, set_payoffs

def price_label(session):
    pr = (session.config.get('price_rule') or 'first').lower()
    return 'first-price' if pr == 'first' else 'second-price'

class Instructions(Page):
    def vars_for_template(self):
        s = self.session
        return dict(
            price_rule=price_label(s),
            matching=(s.config.get('matching') or 'random').lower(),
            tie_rule=(s.config.get('tie_rule') or 'random').lower(),
            chat=bool(s.config.get('chat')),
            ROUNDS=C.NUM_ROUNDS,
        )

class Bid(Page):
    form_model = 'player'
    form_fields = ['bid']
    timeout_seconds = 60
    timeout_submission = {'bid': cu(0)}

    def vars_for_template(self):
        return dict(valuation=self.player.valuation)

class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs

class Results(Page):
    def vars_for_template(self):
        group = self.group
        opp = self.player.get_others_in_group()[0]
        you_won = (group.winner_id_in_group == self.player.id_in_group)
        return dict(
            your_bid=self.player.bid,
            opp_bid=opp.bid,
            valuation=self.player.valuation,
            price=group.price,
            you_won=you_won,
        )

page_sequence = [Instructions, Bid, ResultsWaitPage, Results]
