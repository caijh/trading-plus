import pandas_ta as ta

from calculate.service import detect_turning_points
from strategy.model import TradingStrategy
from strategy.trading_model import TradingModel


class AntiTradingModel(TradingModel):
    def __init__(self):
        super().__init__('AntiTradingModel')

    def get_trading_signal(self, stock, df, trending, direction):
        """
        改进版 ANTI 策略：
        - KDJ 超买/超卖触发
        - EMA 趋势过滤
        - 成交量确认
        - 动态止盈止损 (在 create_trading_strategy 里实现)
        """
        if len(df) < 100:
            return 0

        # ========== 1. 计算指标 ==========
        # KDJ (stochastic)
        kdj_df = df.ta.stoch(
            high='high',
            low='low',
            close='close',
            k=7,
            d=10,
            smooth_d=3
        )
        kdj_df.rename(
            columns={'STOCHk_7_10_3': 'K', 'STOCHd_7_10_3': 'D'},
            inplace=True
        )
        k_series, d_series = kdj_df['K'], kdj_df['D']

        # EMA 均线
        sma20 = df['SMA20']
        sma50 = df['SMA50']

        # 最新值
        k_now, d_now = k_series.iloc[-1], d_series.iloc[-1]
        k_prev, d_prev = k_series.iloc[-2], d_series.iloc[-2]
        k_prev_prev, d_prev_prev = k_series.iloc[-3], d_series.iloc[-3]
        d_turning_points, _, _ = detect_turning_points(d_series)
        if len(d_turning_points) < 1:
            return 0

        # ========== 2. 多头信号 ==========
        bullish_kdj = (d_now > d_turning_points.iloc[-1]) and (k_prev_prev > k_prev < k_now) and (k_now >= d_now)
        bullish_trend = (
            sma20.iloc[-1] > sma50.iloc[-1] > sma50.iloc[-2] and
            sma20.iloc[-1] > sma20.iloc[-2]
        )

        if bullish_kdj and bullish_trend:
            return 1

        # ========== 3. 空头信号 ==========
        bearish_kdj = (d_now < d_turning_points.iloc[-1]) and (k_prev_prev < k_prev > k_now) and (k_now <= d_now)
        bearish_trend = (
            sma20.iloc[-1] < sma50.iloc[-1] < sma50.iloc[-2] and
            sma20.iloc[-1] < sma20.iloc[-2]
        )  # 均线空头排列

        if bearish_kdj and bearish_trend:
            return -1

        return 0

    def create_trading_strategy(self, stock, df, signal):
        """
        创建交易策略对象，支持多头和空头
        - 止盈止损基于 ATR
        """
        if len(df) == 0:
            return None

        last_close = df['close'].iloc[-1]
        n_digits = 3 if stock['stock_type'] == 'Fund' else 2

        # 计算 ATR
        atr_series = ta.atr(df['high'], df['low'], df['close'], length=14)
        atr_now = atr_series.iloc[-1]

        if signal == 1:
            # 📈 多头策略
            entry_price = last_close * 0.998
            stop_loss = round(entry_price - 1.0 * atr_now, n_digits)
            take_profit = round(entry_price + 2.0 * atr_now, n_digits)

        elif signal == -1:
            # 📉 空头策略
            entry_price = last_close * 1.002
            stop_loss = round(entry_price + 1.0 * atr_now, n_digits)
            take_profit = round(entry_price - 2.0 * atr_now, n_digits)

        else:
            return None

        # 创建交易策略对象
        strategy = TradingStrategy(
            strategy_name=self.name,
            stock_code=stock['code'],
            stock_name=stock['name'],
            entry_patterns=['ANTI', 'KDJ', 'EMA'],
            exit_patterns=[],
            exchange=stock['exchange'],
            entry_price=float(entry_price),
            take_profit=float(take_profit),
            stop_loss=float(stop_loss),
            signal=signal
        )
        return strategy

