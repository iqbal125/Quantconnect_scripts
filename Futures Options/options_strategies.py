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


def Strangle(self, chain, sell_dte, delta, proportion):
    target_date = self.Time + dt.timedelta(self.sell_dte)

    # Filter and Sort on given criteria to get target contract
    contracts = [x for x in chain if x.Right == OptionRight.Call] # Filter Call or Puts
    contracts = filter(lambda x: target_date <= x.Expiry, contracts)
    contracts = sorted(contracts, key=lambda x: abs(x.Expiry - target_date)) # Filter Target Expiry
    if len(contracts) == 0: return

    contracts = [x for x in contracts if x.Expiry==contracts[0].Expiry]
    if len(contracts) == 0: return
    self.call = min(contracts, key=lambda x: abs(abs(x.Greeks.Delta) - float(self.delta))) # Get Near to Target Delta

    for i in chain:
        if i.Expiry == self.call.Expiry and i.Right == OptionRight.Put and i.Strike == self.call.Strike:
            self.put = i

    call_symbol = self.call.Symbol
    put_symbol = self.put.Symbol

    self.SetHoldings(call_symbol, proportion, tag=f'Shorted/Long Call Contract with more than {self.sell_dte} DTE')
    self.SetHoldings(put_symbol, proportion, tag=f'Shorted/Long Put Contract with more than {self.sell_dte} DTE')

    return


