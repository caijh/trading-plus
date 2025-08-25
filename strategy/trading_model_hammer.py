from indicator.candlestick import Candlestick
from strategy.model import TradingStrategy
from strategy.trading_model import TradingModel


class HammerTradingModel(TradingModel):
    def __init__(self):
        super().__init__('HammerTradingModel')

    def get_trading_signal(self, stock, df, trending, direction):
        candlestick = Candlestick({"name": "hammer", "description": "锤子线", "signal": 1, "weight": 1}, 1)
        close_price = df.iloc[-1]['close']
        low_price = df.iloc[-1]['low']
        high_price = df.iloc[-1]['high']
        sma20_series = df['SMA20']
        sma50_series = df['SMA50']
        sma120_series = df['SMA120']
        latest_sma20_price = sma20_series.iloc[-1]
        latest_sma50_price = sma50_series.iloc[-1]
        latest_sma120_price = sma120_series.iloc[-1]
        prev_sma120_price = sma120_series.iloc[-2]

        if candlestick.match(stock, df, trending, direction):
            if (low_price <= latest_sma20_price < close_price) \
                or (low_price <= latest_sma50_price < close_price):
                if latest_sma120_price > prev_sma120_price:
                    return 1

        candlestick = Candlestick({"name": "hangingman", "description": "上吊线", "signal": -1, "weight": 0}, -1)
        if candlestick.match(stock, df, trending, direction):
            if (high_price > latest_sma20_price > close_price) \
                or (high_price > latest_sma50_price > close_price):
                if latest_sma120_price < prev_sma120_price:
                    return -1
        return 0

    def create_trading_strategy(self, stock, df, signal):
        last_close = df['close'].iloc[-1]
        n_digits = 3 if stock['stock_type'] == 'Fund' else 2

        if signal == 1:  # 多头
            stop_loss = df.iloc[-1]['low']
            entry_price = last_close
            risk = entry_price - stop_loss
            take_profit = entry_price + 3 * risk  # RR=2:1

        elif signal == -1:  # 空头
            stop_loss = df.iloc[-1]['high']
            entry_price = last_close
            risk = stop_loss - entry_price
            take_profit = entry_price - 3 * risk  # RR=2:1

        else:
            return None

        # 如果 risk <= 0，直接过滤掉无效策略
        if risk <= 0:
            return None

        strategy = TradingStrategy(
            strategy_name=self.name,
            stock_code=stock['code'],
            stock_name=stock['name'],
            entry_patterns=['hammer'] if signal == 1 else ['hangingman'],
            exit_patterns=[],
            exchange=stock['exchange'],
            entry_price=float(round(entry_price, n_digits)),
            take_profit=float(round(take_profit, n_digits)),
            stop_loss=float(round(stop_loss, n_digits)),
            signal=signal
        )
        return strategy

    def get_trading_strategy(self, stock, df):
        trading_signal = self.get_trading_signal(stock, df, stock.get('trending', ''), stock.get('direction', ''))
        if trading_signal == 0:
            return None
        return self.create_trading_strategy(stock, df, trading_signal)
