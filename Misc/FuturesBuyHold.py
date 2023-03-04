# region imports
from AlgorithmImports import *
# endregion

class CasualRedDinosaur(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2022, 6, 9)  # Set Start Date
        self.SetCash(1000000)  # Set Strategy Cash
        self.spy = self.AddEquity("SPY", Resolution.Daily)

        self._continuousContractES = self.AddFuture(Futures.Indices.SP500EMini,
                                                  dataNormalizationMode = DataNormalizationMode.BackwardsRatio,
                                                  dataMappingMode = DataMappingMode.OpenInterest,
                                                  contractDepthOffset = 0)

        self._continuousContractZN = self.AddFuture(Futures.Financials.Y10TreasuryNote,
                                                  dataNormalizationMode = DataNormalizationMode.BackwardsRatio,
                                                  dataMappingMode = DataMappingMode.OpenInterest,
                                                  contractDepthOffset = 0)


        self.Schedule.On(self.DateRules.EveryDay("SPY"), self.TimeRules.AfterMarketOpen("SPY", 5), self.Rebalance)

    def OnData(self, data: Slice):
        pass
    
    def Rebalance(self):
        if self.Portfolio.Invested:
            self.Liquidate(self.esContract.Symbol)
            self.Liquidate(self.znContract.Symbol)

        #self.Debug("Rebalance called at " + str(self.Time))
        self.esContract = self.Securities[self._continuousContractES.Mapped]
        self.znContract = self.Securities[self._continuousContractZN.Mapped]
        self.Debug(str(self.esContract.Symbol) + " " + str(self.znContract.Symbol))

        self.SetHoldings([PortfolioTarget(self.esContract.Symbol, 0.03), PortfolioTarget(self.znContract.Symbol, 0.07), PortfolioTarget("SPY", .9)])

