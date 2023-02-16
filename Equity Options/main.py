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

        option = self.AddOption(self.ticker,Resolution.Hour)
        self.option_symbol = option.Symbol

        # set our strike/expiry filter for this option chain
        # -5 to +5 strikes and 0 to 180 expiry contracts
        option.SetFilter(-5, +5, 0, 180)
        option.PriceModel = OptionPriceModels.CrankNicolsonFD()

        # use the underlying equity as the benchmark
        self.SetBenchmark(self.ticker)

    def AddParameters(self):
        self.sell_dte = SELL_DTE
        self.close_dte = CLOSE_DTE
        self.right = OptionRight.Put
        self.delta = DELTA
        self.iv = IV

    def AddModels(self):
        self.StopType = 'fixed'
        self.rm_model = FixedTrailingStopRMModel(self, maximumDrawdownPercent=1.0)
        self.AddRiskManagement(self.rm_model)

    def OnData(self, slice):        
        self.OnDataEquity(slice)

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
                contracts = [x for x in chain if x.Right == self.right] # Filter Call or Puts
                contracts = filter(lambda x: target_date <= x.Expiry, contracts)                          
                contracts = sorted(contracts, key=lambda x: abs(x.Expiry - target_date)) # Filter Target Expiry
                if(USE_IV): contracts = list(filter(lambda x: abs(x.ImpliedVolatility) > self.iv, contracts)) # Filter IV greater than target
                if len(contracts) == 0: return
                contracts = [x for x in contracts if x.Expiry==contracts[0].Expiry]
                self.contract = min(contracts, key=lambda x: abs(abs(x.Greeks.Delta) - float(self.delta))) # Filter Target Delta
                
                symbol = self.contract.Symbol
                self.MarketOrder(symbol, QUANTITY)

    def OnOrderEvent(self, orderEvent):
        self.Log(f'{orderEvent}')
       
   