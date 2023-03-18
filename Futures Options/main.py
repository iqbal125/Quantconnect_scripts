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
    from options_strategies import Simple, Strangle
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
        #self.AddModels()

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
        if self.Portfolio.Invested: return

        for sym, chain in slice.OptionChains.items():
            self.Strangle(chain, 30, 0.2, 0.05)

    def OnOrderEvent(self, orderEvent):
        self.Log(f'{orderEvent}')
   