import pandas_ta as ta

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
        ema10 = ta.ema(df['close'], length=10)
        ema20 = ta.ema(df['close'], length=20)
        ema50 = ta.ema(df['close'], length=50)

        # 成交量均线
        vol_ma5 = ta.sma(df['volume'], length=5)

        # 最新值
        k_now, d_now = k_series.iloc[-1], d_series.iloc[-1]
        k_prev, d_prev = k_series.iloc[-2], d_series.iloc[-2]
        k_prev_prev, d_prev_prev = k_series.iloc[-3], d_series.iloc[-3]

        vol_now, vol_pre = df['volume'].iloc[-1], df['volume'].iloc[-2]

        # ========== 2. 多头信号 ==========
        bullish_kdj = (d_now > d_prev > d_prev_prev) and (k_prev_prev > k_prev < k_now) and (k_now >= d_now)
        bullish_trend = trending == 'UP'  # 均线多头排列
        bullish_volume = (vol_now < vol_pre)  # 缩量

        if bullish_kdj and bullish_trend and bullish_volume:
            return 1

        # ========== 3. 空头信号 ==========
        bearish_kdj = (d_now < d_prev < d_prev_prev) and (k_prev_prev < k_prev > k_now) and (k_now <= d_now)
        bearish_trend = trending == 'DOWN'  # 均线空头排列
        bearish_volume = (vol_now > vol_pre)  # 放量下跌

        if bearish_kdj and bearish_trend and bearish_volume:
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
            entry_price = last_close
            stop_loss = round(entry_price - 1.5 * atr_now, n_digits)
            take_profit = round(entry_price + 2.5 * atr_now, n_digits)

        elif signal == -1:
            # 📉 空头策略
            entry_price = last_close
            stop_loss = round(entry_price + 1.5 * atr_now, n_digits)
            take_profit = round(entry_price - 2.5 * atr_now, n_digits)

        else:
            return None

        # 创建交易策略对象
        strategy = TradingStrategy(
            strategy_name=self.name,
            stock_code=stock['code'],
            stock_name=stock['name'],
            entry_patterns=['ANTI', 'KDJ', 'EMA', 'VOL', 'ATR'],
            exit_patterns=[],
            exchange=stock['exchange'],
            entry_price=float(entry_price),
            take_profit=float(take_profit),
            stop_loss=float(stop_loss),
            signal=signal
        )
        return strategy

    def get_trading_strategy(self, stock, df):
        """
        根据股票数据和信号生成交易策略
        """
        trading_signal = self.get_trading_signal(stock, df, stock.get('trending', ''), stock.get('direction', ''))
        if trading_signal == 0:
            return None

        return self.create_trading_strategy(stock, df, trading_signal)
