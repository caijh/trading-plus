class TradingModel:
    def __init__(self, name):
        self.name = name

    def get_trading_signal(self, stock, df, signal):
        return 0

    def get_trading_strategy(self, stock, df, signal):
        return None
