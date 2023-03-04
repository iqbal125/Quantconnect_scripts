# region imports
# region imports
from AlgorithmImports import *
# endregion

class CasualRedDinosaur(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2022, 6, 9)  # Set Start Date
        self.SetCash(1000000)  # Set Strategy Cash

        self._continuousContractES = self.AddFuture(Futures.Indices.SP500EMini,
                                                  dataNormalizationMode = DataNormalizationMode.BackwardsRatio,
                                                  dataMappingMode = DataMappingMode.OpenInterest,
                                                  contractDepthOffset = 0)

        self._continuousContractZN = self.AddFuture(Futures.Financials.Y10TreasuryNote,
                                                  dataNormalizationMode = DataNormalizationMode.BackwardsRatio,
                                                  dataMappingMode = DataMappingMode.OpenInterest,
                                                  contractDepthOffset = 0)


    def OnData(self, data: Slice):
        pass
    
    def Rebalance(self):
        if self.Portfolio.Invested:
            self.Liquidate(self.esContract.Symbol)
            self.Liquidate(self.znContract.Symbol)


        self.esContract = self.Securities[self._continuousContractES.Mapped]
        self.znContract = self.Securities[self._continuousContractZN.Mapped]

        self.SetHoldings(self.esContract.Symbol)

