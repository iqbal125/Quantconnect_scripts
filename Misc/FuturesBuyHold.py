# region imports
from AlgorithmImports import *
# endregion

class CasualRedDinosaur(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2015, 6, 9)  # Set Start Date
        self.SetCash(100000)  # Set Strategy Cash
        self.spy = self.AddEquity("SPY", Resolution.Daily)

        self._continuousContractES = self.AddFuture(Futures.Indices.SP500EMini,
                                                  dataNormalizationMode = DataNormalizationMode.BackwardsRatio,
                                                  dataMappingMode = DataMappingMode.OpenInterest,
                                                  contractDepthOffset = 0)

        self._continuousContractZN = self.AddFuture(Futures.Financials.Y10TreasuryNote,
                                                  dataNormalizationMode = DataNormalizationMode.BackwardsRatio,
                                                  dataMappingMode = DataMappingMode.OpenInterest,
                                                  contractDepthOffset = 0)


        self.Schedule.On(self.DateRules.MonthStart("SPY"), self.TimeRules.AfterMarketOpen("SPY", 5), self.Rebalance)

    def OnData(self, data: Slice):
        pass
    
    def Rebalance(self):
        self.Debug("Rebalance called at " + str(self.Time))
        esContract = self.Securities[self._continuousContractES.Mapped]
        znContract = self.Securities[self._continuousContractZN.Mapped]

        self.SetHoldings(esContract.Symbol, .05)
        # self.SetHoldings(znContract.Symbol, .7)
