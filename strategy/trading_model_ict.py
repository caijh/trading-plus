import numpy as np
import pandas_ta as ta

from strategy.model import TradingStrategy
from strategy.trading_model import TradingModel


class ICTTradingModel(TradingModel):
    def __init__(self):
        super().__init__('ICTTradingModel')

    def get_trading_signal(self, stock, df, trending, direction):
        """
        优化版 ICT 策略：
        - 趋势过滤 (EMA)
        - 有效 FVG (需大于 ATR*0.2)
        - MSS + 回测确认
        """

        if len(df) < 200:  # 需要足够数据来计算EMA/ATR
            return 0

        # 1️⃣ 趋势过滤：EMA200 确定大方向
        df['ema200'] = ta.ema(df['close'], length=200)
        trend_up = df['close'].iloc[-1] > df['ema200'].iloc[-1]
        trend_down = df['close'].iloc[-1] < df['ema200'].iloc[-1]

        # 2️⃣ ATR 波动率，用于FVG过滤
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)

        # 3️⃣ MSS（复杂版市场结构转变）检测
        df['swing_high'] = df['high'].rolling(window=5, center=True).apply(
            lambda x: x.iloc[2] if x.iloc[2] == x.max() else np.nan
        )
        df['swing_low'] = df['low'].rolling(window=5, center=True).apply(
            lambda x: x.iloc[2] if x.iloc[2] == x.min() else np.nan
        )

        last_swing_high = df['swing_high'].dropna().iloc[-1] if not df['swing_high'].dropna().empty else None
        last_swing_low = df['swing_low'].dropna().iloc[-1] if not df['swing_low'].dropna().empty else None

        high_1, low_1, close_1, open_1 = df['high'].iloc[-1], df['low'].iloc[-1], df['close'].iloc[-1], df['open'].iloc[
            -1]
        high_3, low_3 = df['high'].iloc[-3], df['low'].iloc[-3]
        atr = df['atr'].iloc[-1]

        # 4️⃣ 公平价值缺口 (FVG) 判断 + 有效性过滤
        bullish_fvg = (low_1 > high_3) and ((low_1 - high_3) > 0.2 * atr)
        bearish_fvg = (high_1 < low_3) and ((low_3 - high_1) > 0.2 * atr)

        # 5️⃣ 交易逻辑：必须符合趋势 + FVG + MSS
        # 📈 多头信号
        if bullish_fvg and trend_up and last_swing_high and (high_1 > last_swing_high) and (close_1 > open_1):
            return 1

        # 📉 空头信号
        if bearish_fvg and trend_down and last_swing_low and (low_1 < last_swing_low) and (close_1 < open_1):
            return -1

        return 0

    def create_trading_strategy(self, stock, df, signal):
        """
        策略优化：
        - 入场价 = 当前收盘价
        - 止损 = 最近 swing high/low 或 FVG 边界
        - 止盈 = RR = 2:1
        """
        if len(df) < 20:
            return None

        last_close = df['close'].iloc[-1]
        n_digits = 3 if stock['stock_type'] == 'Fund' else 2

        if signal == 1:  # 多头
            stop_loss = df['swing_low'].dropna().iloc[-1] if not df['swing_low'].dropna().empty else df['low'].iloc[
                -5:].min()
            entry_price = last_close
            risk = entry_price - stop_loss
            take_profit = entry_price + 2 * risk  # RR=2:1

        elif signal == -1:  # 空头
            stop_loss = df['swing_high'].dropna().iloc[-1] if not df['swing_high'].dropna().empty else df['high'].iloc[
                -5:].max()
            entry_price = last_close
            risk = stop_loss - entry_price
            take_profit = entry_price - 2 * risk  # RR=2:1
        else:
            return None

        strategy = TradingStrategy(
            strategy_name=self.name,
            stock_code=stock['code'],
            stock_name=stock['name'],
            entry_patterns=['ICT', 'FVG', 'MSS'],
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
