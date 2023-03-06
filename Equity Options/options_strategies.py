#region imports
from AlgorithmImports import *
import datetime as dt
#endregion


def Simple(self, chain, sell_dte, right, delta):
    target_date = self.Time + dt.timedelta(self.sell_dte)
    # Filter Call or Puts
    contracts = [x for x in chain if x.Right == self.right]

    # Filter Target Expiry
    contracts = filter(lambda x: target_date <= x.Expiry, contracts)
    contracts = sorted(contracts, key=lambda x: abs(x.Expiry - target_date))
    contracts = [x for x in contracts if x.Expiry==contracts[0].Expiry]

    #Find contracts
    if len(contracts) == 0: return

    # Filter Target Delta
    self.contract = min(contracts, key=lambda x: abs(abs(x.Greeks.Delta) - float(self.delta)))

    symbol = self.contract.Symbol
    self.MarketOrder(symbol, 1)

# def Straddle:
# def Strangle:


