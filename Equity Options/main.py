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


#endregion

class OptionsEquitiesTemplate(QCAlgorithm):
    from options_strategies import Simple, Strangle
    # ==================================================================================
    # Main entry point for the algo
    # ==================================================================================
    def Initialize(self):

        # Set Parameters of the backtest
        self.SetStartDate(STARTDATE_YEAR, STARTDATE_MONTH, STARTDATE_DAY)
        # self.SetEndDate(END_DATE_YEAR, END_DATE_MONTH, END_DATE_DAY) # In case no end date is specified, backtest is run till more recent data
        self.SetCash(CASH)

        # We need to add options data for the given ticker
        self.ticker = TICKER
        #self.AddModels()
        self.AddParameters()

        option = self.AddOption(self.ticker, Resolution.Hour)
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
        self.right = OptionRight.Call
        self.delta = DELTA
        self.iv = IV


    def AddModels(self):
        self.StopType = 'fixed'
        self.rm_model = FixedTrailingStopRMModel(self, maximumDrawdownPercent=1.0)
        self.AddRiskManagement(self.rm_model)

    def OnData(self, slice):
        self.OnDataEquity(slice)

    def OnDataEquity(self,slice):
        if self.Portfolio.Invested: return

        # Get the Option Chain and search for option of Target Expiry and Delta
        chain = slice.OptionChains.get(self.option_symbol)
        if not chain: return

        self.Strangle(chain, 30, 0.2, 0.5)


    def OnOrderEvent(self, orderEvent):
        self.Log(f'{orderEvent}')
    