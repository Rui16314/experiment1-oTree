from otree.api import Bot, currency_range, Currency as cu
from .models import C


class PlayerBot(Bot):
    def play_round(self):
        # See your valuation; bid a fraction of it.
        val = self.player.valuation or cu(0)
        my_bid = round(float(val) * 0.7, 2)
        yield self.pages.Instructions
        yield self.pages.Bid, dict(bid=cu(my_bid))
        yield self.pages.Results

