from strategy.model import TradingStrategy
from strategy.trading_model import TradingModel


class IndicatorTradingModel(TradingModel):
    def __init__(self):
        """
         k线与指标共振策略
        """
        super().__init__('IndicatorTradingModel')

    def get_trading_signal(self, stock, df, trending, direction):
        candlestick_signal = stock['candlestick_signal']
        indicator_signal = stock['indicator_signal']
        patterns = []
        patterns.extend(stock['primary_patterns'])
        patterns.extend(stock['secondary_patterns'])
        if candlestick_signal == 1 and indicator_signal == 1:
            return 1
        elif candlestick_signal == -1 and indicator_signal == -1:
            return -1
        return 0

    def create_trading_strategy(self, stock, df, signal):
        patterns = []
        if signal == 1:  # 多头
            stop_loss = stock['support'] * 0.998
            entry_price = stock['support']
            target_high = stock['resistance']
            take_profit = target_high * 0.998
        elif signal == -1:  # 空头
            stop_loss = stock['resistance'] * 1.002
            entry_price = stock['resistance']
            target_low = stock['support']
            take_profit = target_low * 1.002
        else:
            return None

        patterns.extend([pattern['label'] for pattern in stock['candlestick_patterns']])
        patterns.extend(stock['primary_patterns'])
        patterns.extend(stock['secondary_patterns'])
        n_digits = 3 if stock['stock_type'] == 'Fund' else 2
        code = stock['code']
        name = stock['name']
        # ---- 返回策略 ----
        strategy = TradingStrategy(
            strategy_name=self.name,
            stock_code=code,
            stock_name=name,
            entry_patterns=patterns,
            exit_patterns=[],
            exchange=stock['exchange'],
            entry_price=float(round(entry_price, n_digits)),
            take_profit=float(round(take_profit, n_digits)),
            stop_loss=float(round(stop_loss, n_digits)),
            signal=signal
        )
        return strategy
