# experiment1/pages.py
from otree.api import Page, WaitPage
from .models import C

class Instructions(Page):
    # Show once at the very beginning
    def is_displayed(player):
        return player.round_number == 1

    def vars_for_template(player):
        cfg = player.session.config
        price = cfg.get('price_rule', C.PRICE_RULE)
        matching = cfg.get('matching', C.MATCHING)
        return dict(
            price_rule_text='first-price (highest bid pays)' if price == 'first'
            else 'second-price (winner pays the other bid)',
            matching_text='random' if matching == 'random' else 'fixed',
        )

# NEW: wait page that assigns valuations before Bid each round
class RoundStart(WaitPage):
    after_all_players_arrive = 'assign_valuations'

class Bid(Page):
    form_model = 'player'
    form_fields = ['bid']
    timeout_seconds = 60

    def vars_for_template(player):
        # valuation is guaranteed to be set by RoundStart
        return dict(valuation=player.valuation)

class ResultsWaitPage(WaitPage):
    after_all_players_arrive = 'set_payoffs'

class Results(Page):
    pass

page_sequence = [Instructions, RoundStart, Bid, ResultsWaitPage, Results]


page_sequence = [Instructions, Bid, ResultsWaitPage, Results]

