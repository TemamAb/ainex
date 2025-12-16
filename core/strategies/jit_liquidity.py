import math

class JITManager:
    def __init__(self):
        self.tick_spacing = 60 # Uniswap V3 default for volatile pairs
        
    def calculate_optimal_range(self, current_price, whale_impact_percent):
        """
        Calculates the tick range to capture a specific whale transaction.
        """
        price_lower = current_price
        price_upper = current_price * (1 + whale_impact_percent)
        
        tick_lower = self._price_to_tick(price_lower)
        tick_upper = self._price_to_tick(price_upper)
        
        return tick_lower, tick_upper

    def _price_to_tick(self, price):
        return int(math.log(price, 1.0001))
