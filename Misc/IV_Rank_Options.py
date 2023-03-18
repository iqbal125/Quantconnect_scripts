#region imports
from AlgorithmImports import *
#endregion
import pandas as pd
import operator
from functools import partial
from QuantConnect.Securities.Option import OptionPriceModels
 
class ParticleCalibratedCoil(QCAlgorithm):
 
    def Initialize(self):
 
        '''
            Parameters for adjusting
        '''
        self.numberOfLiquidStocks = 100 # Controls the number of stocks in play
 
 
        '''
            Backtesting variables
        '''
        self.SetStartDate(2019, 10, 18)
        #self.SetEndDate(2019, 12, 18)
        self.SetCash(1000000)
 
        '''
            Algorithm variables
        '''
        self.UniverseSettings.Resolution = Resolution.Daily
        self.AddUniverse(self.CoarseSelectionFilter)
        self.SetSecurityInitializer(lambda x: x.SetDataNormalizationMode(DataNormalizationMode.Raw))
 
        self.data = {}
 
 
    def CoarseSelectionFilter(self, coarse):
        '''
            1. Sorts each element of the coarse object by dollar volume
            2. Returns a list of coarse object, limited to top 100 highest volume
            3. Returns a list of symbols we want to initialise into the algorithm
        '''
        coarse = [x for x in coarse if x.HasFundamentalData]
        self.sortedByDollarVolume = sorted(coarse, key=lambda c: c.DollarVolume, reverse=True)
        self.topHundredMostLiquid = self.sortedByDollarVolume[:self.numberOfLiquidStocks]
 
        return [stock.Symbol for stock in self.topHundredMostLiquid]
 
    def OnSecuritiesChanged (self,changes):
 
        '''
            For any new securities added into the universe
            If the security is an underlying
            Subscribe to the option chains
 
            For any securities we want removed from the universe
            Remove the underlying and then remove the options
 
            For each new secury added into the universe
            If there is not yet one
            Create a standard deviation indicator
        '''
        for change in changes.AddedSecurities:
            self.data[change.Symbol] = SymbolData(self, change.Symbol)
            #self.Debug("Added " + str(change.Symbol) + str(self.Time))
 
        for change in changes.RemovedSecurities:
            self.RemoveSecurity(change.Symbol)
            #self.Debug("Removed " + str(change.Symbol) + str(self.Time))
            self.data.pop(change.Symbol)
 
    def OnData(self, data: Slice):
 
        '''
            For each OptionChain, the key is the underlying symbol object, while the
            value is the option chain.
            For each chain in OptionChains, each chain represents the entire chain of option contracts
            for the underlying security.
        '''
 
        #self.Debug(len(self.data.values()))
        readyStocks = [x for x in self.data.values() if x.ready]
        #self.Debug(len(readyStocks))
 
        topIVMetricStocks = sorted(readyStocks, key= lambda x: x.IVRank, reverse=True)[:5]
        for x in topIVMetricStocks:
            self.Debug(str(x.symbol) + " " + str(x.IVRank))
 
 
class SymbolData(object):
    def __init__(self, algorithm, symbol):
        self.symbol = symbol
        self.algorithm = algorithm
        self.volatility = algorithm.STD(symbol, 252, Resolution.Daily)
        self.volWindow = RollingWindow[float](252)
        self.volatility.Updated += self.OnVolUpdated
        self.ready = False
 
    def OnVolUpdated(self, sender, updated):
 
        self.volWindow.Add(self.volatility.Current.Value)
 
        if self.volatility.IsReady and self.volWindow.IsReady:
            self.ready = True
            #self.algorithm.Debug(str(self.symbol) + " " + str(self.algorithm.Time))
        else:
            self.ready = False
 
        if self.ready == True:
            #IV Rank calculation
            minimum = min(self.volWindow)
            maximum = max(self.volWindow)
            #self.algorithm.Debug(str(self.symbol) + " " + str(minimum) + " " + str(maximum))
            self.IVRank = (self.volWindow[0] - minimum) / (maximum - minimum)
 
            #IV Percentile calculation
            count = 0
            currentVol = self.volWindow[0]
            for x in self.volWindow:
                if x < currentVol:
                    count += 1
 
            self.IVPercentile = count / 252
 
 
  # if(USE_IV): contracts = list(filter(lambda x: abs(x.ImpliedVolatility) > self.iv, contracts))
