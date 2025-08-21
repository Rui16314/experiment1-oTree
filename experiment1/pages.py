from otree.api import *
from .models import C, Player, Group, Subsession, set_payoffs

# If you added the instructions.css and images in _static/, you can reference them
# in your templates with {{ static('instructions.css') }} and {{ static('img/...') }}.


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
    # If they time out, store bid=0 so we never get None at payoff time.
    timeout_submission = {'bid': cu(0)}

    def vars_for_template(player: Player):
        return dict(valuation=player.valuation)


class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs


class Results(Page):
    def vars_for_template(player: Player):
        group = player.group
        opponent = player.get_others_in_group()[0]
        winner = group.winner_id_in_group
        you_won = (winner == player.id_in_group)
        return dict(
            your_bid=player.bid,
            opp_bid=opponent.bid,
            valuation=player.valuation,
            price=group.price,
            you_won=you_won,
        )


page_sequence = [
    Instructions,
    Bid,
    ResultsWaitPage,
    Results,
]

