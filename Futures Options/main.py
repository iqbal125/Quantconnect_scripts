#region imports
from AlgorithmImports import *
from QuantConnect.Securities.Option import OptionPriceModels
from QuantConnect.Indicators import *
from datetime import timedelta, datetime
import numpy as np
from statistics import median
from QuantConnect.DataSource import *
from constants import *
import datetime as dt
from risk_management import *
#endregion

class OptionsFuturesTemplate(QCAlgorithm):

    # ==================================================================================
    # Main entry point for the algo     
    # ==================================================================================
    def Initialize(self):

        # Set Parameters of the backtest 
        self.SetStartDate(STARTDATE_YEAR, STARTDATE_MONTH, STARTDATE_DAY)
        #self.SetEndDate(END_DATE_YEAR, END_DATE_MONTH, END_DATE_DAY) # In case no end date is specified, backtest is run till more recent data
        self.SetCash(CASH)

        # We need to add options data for the given ticker
        self.ticker = TICKER
        self.AddParameters()
        self.AddModels()

        #Adding Instruments 
        self.futureES = self.AddSecurity(SecurityType.Future, Futures.Indices.SP500EMini, Resolution.Hour)
        self.futureES.SetFilter(timedelta(0), timedelta(182))

        self.AddFutureOption(self.futureES.Symbol, lambda option_filter_universe: option_filter_universe.Strikes(-3, 3))
        self.SetBenchmark(self.futureES.Symbol)


    def AddParameters(self):
        self.sell_dte = SELL_DTE
        self.close_dte = CLOSE_DTE
        self.delta = DELTA
        self.iv = IV

    def AddModels(self):
        self.StopType = 'fixed'
        self.rm_model = FixedTrailingStopRMModel(self, maximumDrawdownPercent=MAX_DRAWDOWN)
        self.AddRiskManagement(self.rm_model)

    def OnData(self, slice):
        self.OnDataFuture(slice)

    def OnDataFuture(self,slice):
        if self.Portfolio.Invested:
            # If we are already invested, we'll wait for DTE to reach less or equal to Close DTE
            if (self.call.Expiry - self.Time).days <= self.close_dte:
                self.SetHoldings(self.call.Symbol, PROPORTION*-1, tag='Liquidated Call: Reached Target DTE')
                self.SetHoldings(self.put.Symbol, PROPORTION*-1, tag='Liquidated Put: Reached Target DTE')

        else:
            # Iterate through all option chains of all futures and
            # select option which has minimum distance to Expiry of self.sell_dte
            for sym, chain in slice.OptionChains.items():
                if chain:
                    target_date = self.Time + dt.timedelta(self.sell_dte)

                    # Filter and Sort on given criteria to get target contract
                    contracts = [x for x in chain if x.Right == OptionRight.Call] # Filter Call or Puts
                    contracts = filter(lambda x: target_date <= x.Expiry, contracts)
                    contracts = sorted(contracts, key=lambda x: abs(x.Expiry - target_date)) # Filter Target Expiry
                    if len(contracts) == 0: continue

                    contracts = [x for x in contracts if x.Expiry==contracts[0].Expiry]
                    if(USE_IV): contracts = list(filter(lambda x: abs(x.ImpliedVolatility) > self.iv, contracts)) # Filter IV greater than target
                    if len(contracts) == 0: continue
                    self.call = min(contracts, key=lambda x: abs(abs(x.Greeks.Delta) - float(self.delta))) # Get Near to Target Delta

                    for i in chain:
                        if i.Expiry == self.call.Expiry and i.Right == OptionRight.Put and i.Strike == self.call.Strike:
                            self.put = i

                    call_symbol = self.call.Symbol
                    put_symbol = self.put.Symbol

                    self.SetHoldings(call_symbol, PROPORTION, tag=f'Shorted/Long Call Contract with more than {self.sell_dte} DTE')
                    self.SetHoldings(put_symbol, PROPORTION, tag=f'Shorted/Long Put Contract with more than {self.sell_dte} DTE')

                    break

    def OnOrderEvent(self, orderEvent):
        self.Log(f'{orderEvent}')
       
   