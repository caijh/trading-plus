import pandas_ta as ta

from indicator.candlestick import Candlestick
from strategy.model import TradingStrategy
from strategy.trading_model import TradingModel


class HammerTradingModel(TradingModel):
    def __init__(self):
        """
        初始化锤子线交易模型。
        """
        super().__init__('HammerTradingModel')

    def get_trading_signal(self, stock, df, trending, direction):
        """
        根据锤子线或上吊线形态，结合均线趋势和成交量判断交易信号。

        参数:
            stock (dict): 股票信息字典，包含股票代码、名称等。
            df (pandas.DataFrame): 包含历史价格数据的 DataFrame，需包含 'close', 'low', 'high', 'SMA20', 'SMA50', 'SMA120' 列。
            trending (str): 当前趋势状态（如 'UP'、'DOWN'）。
            direction (str): 当前方向（'UP' 表示上涨趋势，'DOWN' 表示下跌趋势）。

        返回:
            int: 交易信号：
                - 1 表示多头信号（买入）；
                - -1 表示空头信号（卖出）；
                - 0 表示无信号。
        """
        # ---- 均线准备 ----
        sma20_series = df['SMA20']
        sma50_series = df['SMA50']
        sma120_series = df['SMA120']
        latest_sma20_price = sma20_series.iloc[-1]
        latest_sma50_price = sma50_series.iloc[-1]
        latest_sma120_price = sma120_series.iloc[-1]
        prev_sma120_price = sma120_series.iloc[-2]

        # ---- 当日价格 ----
        close_price = df.iloc[-1]['close']
        low_price = df.iloc[-1]['low']
        high_price = df.iloc[-1]['high']

        # ---- Hammer (多头) ----
        candlestick = Candlestick({"name": "hammer", "description": "锤子线", "signal": 1, "weight": 1}, 1)
        if candlestick.match(stock, df, trending, direction) and direction == 'UP':
            if (low_price <= latest_sma20_price < close_price) \
                or (low_price <= latest_sma50_price < close_price):
                if latest_sma120_price > prev_sma120_price:  # 长期趋势向上
                    return 1

        # ---- Hangingman (空头) ----
        candlestick = Candlestick({"name": "hangingman", "description": "上吊线", "signal": -1, "weight": 0}, -1)
        if candlestick.match(stock, df, trending, direction) and direction == 'DOWN':
            if (high_price >= latest_sma20_price > close_price) \
                or (high_price >= latest_sma50_price > close_price):
                if latest_sma120_price < prev_sma120_price:  # 长期趋势向下
                    return -1

        return 0

    def create_trading_strategy(self, stock, df, signal):
        """
        根据交易信号生成具体的交易策略，包括入场价、止盈价和止损价。

        参数:
            stock (dict): 股票信息字典，包含股票代码、名称、类型等。
            df (pandas.DataFrame): 包含历史价格数据的 DataFrame。
            signal (int): 交易信号（1 表示多头，-1 表示空头）。

        返回:
            TradingStrategy: 交易策略对象，若信号无效或风控失败则返回 None。
        """
        last_close = df['close'].iloc[-1]
        n_digits = 3 if stock['stock_type'] == 'Fund' else 2

        # ---- ATR 动态止盈止损 ----
        atr = ta.atr(df['high'], df['low'], df['close'], length=14).iloc[-1]

        if signal == 1:  # 多头
            stop_loss = df.iloc[-1]['low']
            entry_price = last_close
            take_profit = entry_price + 2 * atr  # 目标利润 = 2 ATR

        elif signal == -1:  # 空头
            stop_loss = df.iloc[-1]['high']
            entry_price = last_close
            take_profit = entry_price - 2 * atr  # 目标利润 = 2 ATR

        else:
            return None

        # ---- 风控校验 ----
        risk = abs(entry_price - stop_loss)
        if risk <= 0:
            return None

        # ---- 返回策略 ----
        strategy = TradingStrategy(
            strategy_name=self.name,
            stock_code=stock['code'],
            stock_name=stock['name'],
            entry_patterns=['hammer', 'VOL', 'SMA'] if signal == 1 else ['hangingman', 'VOL', 'SMA'],
            exit_patterns=[],
            exchange=stock['exchange'],
            entry_price=float(round(entry_price, n_digits)),
            take_profit=float(round(take_profit, n_digits)),
            stop_loss=float(round(stop_loss, n_digits)),
            signal=signal
        )
        return strategy

    def get_trading_strategy(self, stock, df):
        """
        获取完整的交易策略，包括信号判断和策略生成。

        参数:
            stock (dict): 股票信息字典。
            df (pandas.DataFrame): 包含历史价格数据的 DataFrame。

        返回:
            TradingStrategy: 完整的交易策略对象，若无有效信号则返回 None。
        """
        trading_signal = self.get_trading_signal(stock, df, stock.get('trending', ''), stock.get('direction', ''))
        if trading_signal == 0:
            return None
        return self.create_trading_strategy(stock, df, trading_signal)
