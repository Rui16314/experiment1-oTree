from otree.api import *
from .models import C, Player, Group, Subsession, set_payoffs, cu


def price_label(session):
    pr = (session.config.get('price_rule') or 'first').lower()
    return 'first-price' if pr == 'first' else 'second-price'


class Instructions(Page):
    def vars_for_template(player: Player):
        s = player.session
        return dict(
            price_rule=price_label(s),
            matching=(s.config.get('matching') or 'random').lower(),
            tie_rule=(s.config.get('tie_rule') or 'random').lower(),
            ROUNDS=C.NUM_ROUNDS,
        )


class Bid(Page):
    form_model = 'player'
    form_fields = ['bid']
    timeout_seconds = 60
    # If they time out, store a zero bid so payoff code never sees None.
    timeout_submission = {'bid': cu(0)}

    def vars_for_template(player: Player):
        # Keep template simple; valuation is guaranteed non-None by creating_session
        return dict(valuation=player.valuation)


class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs


class Results(Page):
    def vars_for_template(player: Player):
        other = player.get_others_in_group()[0]
        group = player.group
        return dict(
            your_bid   = player.bid,
            opp_bid    = other.bid,
            valuation  = player.valuation,
            price      = group.price,
            you_won    = (group.winner_id_in_group == player.id_in_group),
        )


page_sequence = [Instructions, Bid, ResultsWaitPage, Results]

