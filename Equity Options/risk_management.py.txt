#region imports
from AlgorithmImports import *
#endregion

class FixedTrailingStopRMModel(RiskManagementModel):
    '''Provides an implementation of IRiskManagementModel that limits the maximum possible loss
    measured from the highest unrealized profit'''
    def __init__(self, algo, maximumDrawdownPercent = 0.05):
        '''Initializes a new instance of the TrailingStopRiskManagementModel class
        Args:
            maximumDrawdownPercent: The maximum percentage drawdown allowed for algorithm portfolio compared with the highest unrealized profit, defaults to 5% drawdown'''
        self.maximumDrawdownPercent = abs(maximumDrawdownPercent)
        self.anchors = dict()
        self.algo = algo

    def ManageRisk(self, algorithm, targets):
        '''Manages the algorithm's risk at each time step
        Args:
            algorithm: The algorithm instance
            targets: The current portfolio targets to be assessed for risk
            
        Explanation:
            value is used as anchor in below code. Whenever the profitPercent is greater than the anchor(value),
            value is updated to new profit.
            For e.g. a profit of 0.01% will update the anchor from 0 to 0.01% and hence new stop-loss will be:
            0.01% - 0.02% = -0.01%
        
        '''

        riskAdjustedTargets = list()
        if self.algo.IsWarmingUp:
            return riskAdjustedTargets

        for kvp in algorithm.Securities:
            symbol = kvp.Key
            security = kvp.Value

            # Remove if not invested
            if not security.Invested:
                self.anchors.pop(symbol, None)
                continue

            profitPercent = security.Holdings.UnrealizedProfitPercent # for example: 0.017

            if self.algo.StopType == 'trailing':                

                # Add newly invested securities
                value = self.anchors.get(symbol)
                if value == None:
                    newValue = profitPercent if profitPercent > 0 else 0 
                    self.anchors[symbol] = newValue # self.trailing[symbol] = 0
                    continue

                # Check for new high and update
                if value < profitPercent: # if old trailing value = 0 is less than new profitPercent = 0.017
                    self.anchors[symbol] = profitPercent # update trailing percent to new profitPercent = 0.017
                    continue

                # value = 0
                # profitPercent = 0.017
                # self.trailing[symbol] = 0.017
                
                # If unrealized profit percent deviates from local max for more than affordable percentage
                # if 0.017 < 0 - 0.02
                threshold = value - self.maximumDrawdownPercent

            else:
                stop_pct = self.maximumDrawdownPercent*-1
                target_pct = self.maximumDrawdownPercent

            if (profitPercent < stop_pct) or (profitPercent > target_pct):
                # liquidate
                
                self.algo.Log('Liquidating as either stop-loss or target was hit')
                riskAdjustedTargets.append(PortfolioTarget(symbol, 0))

        return riskAdjustedTargets
