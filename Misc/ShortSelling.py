# Long-Short static sample portfolio

from AlgorithmImports import *

# -------------------------------------------------------------------------------------------------------
LONGS = ['TYD']; SHORTS = ['SQQQ']; LEV = 0.66; 
# -------------------------------------------------------------------------------------------------------

class PositiveMarSectorETF(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2014, 1, 1)
        self.SetEndDate(2019, 1, 1)
        self.SetCash(10000) 
        res = Resolution.Minute
        self.Longs = [self.AddEquity(ticker, res).Symbol for ticker in LONGS]
        self.Shorts = [self.AddEquity(ticker, res).Symbol for ticker in SHORTS]
        self.Schedule.On(self.DateRules.MonthStart(self.Longs[0]), self.TimeRules.AfterMarketOpen(self.Longs[0], 30), self.rebalance)

    
    def rebalance(self):
        for sec in self.Longs:
            self.SetHoldings(sec, .5/len(self.Longs))                    
        for sec in self.Shorts:
            self.SetHoldings(sec, -0.5*LEV/len(self.Shorts))  

