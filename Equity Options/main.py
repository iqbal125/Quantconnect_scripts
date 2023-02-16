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
        self.SetStartDate(2022, 6, 1)
        # self.SetEndDate(2022, 10, 31) # In case no end date is specified, backtest is run till more recent data
        self.SetCash(CASH)

        # We need to add options data for the given ticker
        self.ticker = TICKER
        self.AddParameters()
        self.AddModels()

        if TICKER_TYPE == 'FUTURE':
            #Adding Instruments 
            self.futureES = self.AddSecurity(SecurityType.Future, Futures.Indices.SP500EMini, Resolution.Hour)
            self.futureES.SetFilter(timedelta(0), timedelta(182))
            if self.right == OptionRight.Call:
                self.AddFutureOption(self.futureES.Symbol, lambda option_filter_universe: option_filter_universe.Strikes(-3, 3).CallsOnly())            
            else:
                self.AddFutureOption(self.futureES.Symbol, lambda option_filter_universe: option_filter_universe.Strikes(-3, 3).PutsOnly())            
            self.SetBenchmark(self.futureES.Symbol)
        else:

            option = self.AddOption(self.ticker,Resolution.Hour)
            self.option_symbol = option.Symbol

            # set our strike/expiry filter for this option chain
            # -5 to +5 strikes and 0 to 180 expiry contracts
            option.SetFilter(-5, +5, 0, 180)
            option.PriceModel = OptionPriceModels.CrankNicolsonFD()

            # use the underlying equity as the benchmark
            self.SetBenchmark(self.ticker)

    def AddParameters(self):
        self.sell_dte = 45
        self.close_dte = 21
        self.right = OptionRight.Call
        self.delta = -0.5
        self.iv = 0.01

    def AddModels(self):
        self.StopType = 'fixed'
        self.rm_model = FixedTrailingStopRMModel(self, maximumDrawdownPercent=1.0)
        self.AddRiskManagement(self.rm_model)

    def OnData(self, slice):        
        self.OnDataFuture(slice) if TICKER_TYPE == 'FUTURE' else self.OnDataEquity(slice)

    def OnDataEquity(self,slice):
        if self.Portfolio.Invested: 
            # If we are already invested, we'll wait for DTE to reach less or equal to Close DTE
            if (self.contract.Expiry - self.Time).days <= self.close_dte:
                self.MarketOrder(self.contract.Symbol, 1,tag='Liquidated: Reached Target DTE')            

        else:
            # Get the Option Chain and search for option of Target Expiry and Delta
            chain = slice.OptionChains.get(self.option_symbol)
            if chain:
                target_date = self.Time + dt.timedelta(self.sell_dte)                                    
                contracts = sorted(contracts, key=lambda x: abs(x.Expiry - target_date)) # Filter Target Expiry
                if len(contracts) == 0: return
                contracts = [x for x in contracts if x.Expiry==contracts[0].Expiry]
                self.contract = min(contracts, key=lambda x: abs(abs(x.Greeks.Delta) - float(self.delta))) # Filter Target Delta
                
                symbol = self.contract.Symbol
                self.MarketOrder(symbol, -1)

    def OnDataFuture(self,slice):
        if self.Portfolio.Invested: 
            # If we are already invested, we'll wait for DTE to reach less or equal to Close DTE
            if (self.contract.Expiry - self.Time).days <= self.close_dte:
                self.MarketOrder(self.contract.Symbol, 1,tag='Liquidated: Reached Target DTE')            

        else:

            # Iterate through all option chains of all futures and 
            # select option which has minimum distance to Expiry of self.sell_dte
            for sym, chain in slice.OptionChains.items():

                if chain:
                    target_date = self.Time + dt.timedelta(self.sell_dte)

                    # Filter and Sort on given criteria to get target contract
                    contracts = [x for x in chain if x.Right == self.right] # Filter Call or Puts
                    contracts = filter(lambda x: target_date <= x.Expiry, contracts)                                    
                    contracts = sorted(contracts, key=lambda x: abs(x.Expiry - target_date)) # Filter Target Expiry
                    if len(contracts) == 0: continue

                    contracts = [x for x in contracts if x.Expiry==contracts[0].Expiry]
                    contracts = list(filter(lambda x: abs(x.ImpliedVolatility) > self.iv, contracts)) # Filter IV greater than target
                    if len(contracts) == 0: continue
                    self.contract = min(contracts, key=lambda x: abs(abs(x.Greeks.Delta) - float(self.delta))) # Get Near to Target Delta
                                        
                    symbol = self.contract.Symbol
                    self.MarketOrder(symbol, -1,tag=f'Shorted Contract with more than {self.sell_dte} DTE')
                    break


    def OnOrderEvent(self, orderEvent):
        self.Log(f'{orderEvent}')
       
   