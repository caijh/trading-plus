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

        # 1️⃣ 趋势过滤
        trend_up = True if stock['trending'] == 'UP' else False
        trend_down = True if stock['trending'] == 'DOWN' else False

        # 2️⃣ ATR 波动率，用于FVG过滤
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        atr = df['atr'].iloc[-1]

        # 3️⃣ MSS（市场结构转变）检测，改用 turning
        swing_high_points = df[df['turning'] == -1][['high', 'low', 'close', 'open']]
        swing_low_points = df[df['turning'] == 1][['high', 'low', 'close', 'open']]

        last_swing_high = swing_high_points['high'].iloc[-1] if not swing_high_points.empty else None
        last_swing_low = swing_low_points['low'].iloc[-1] if not swing_low_points.empty else None

        high_1, low_1, close_1, open_1 = df['high'].iloc[-1], df['low'].iloc[-1], df['close'].iloc[-1], df['open'].iloc[
            -1]
        high_3, low_3 = df['high'].iloc[-3], df['low'].iloc[-3]

        # 最近一次突破
        last_close = df['close'].iloc[-1]
        bos_up = last_swing_high and (last_close > last_swing_high)
        bos_down = last_swing_low and (last_close < last_swing_low)

        # 4️⃣ 公平价值缺口 (FVG) 判断 + 有效性过滤
        fvg_threshold = 0.3 if stock['stock_type'] == 'Fund' else 0.1
        bullish_fvg = (low_1 > high_3) and ((low_1 - high_3) > fvg_threshold * atr)
        bearish_fvg = (high_1 < low_3) and ((low_3 - high_1) > fvg_threshold * atr)

        # 5️⃣ 交易逻辑：必须符合趋势 + FVG + MSS
        # 📈 多头信号
        if bullish_fvg and trend_up and bos_up and (close_1 > open_1):
            return 1

        # 📉 空头信号
        if bearish_fvg and trend_down and bos_down and (close_1 < open_1):
            return -1

        return 0

    def create_trading_strategy(self, stock, df, signal):
        """
        策略优化：
        - 入场价 = 当前收盘价
        - 止损 = 最近 swing high/low (来自 turning)
        - 止盈 = RR = 2:1
        """
        if len(df) < 20:
            return None

        last_close = df['close'].iloc[-1]
        n_digits = 3 if stock['stock_type'] == 'Fund' else 2

        swing_highs = df[df['turning'] == -1]
        swing_lows = df[df['turning'] == 1]

        # 从 turning 提取最近拐点
        last_swing_high = swing_highs['high'].iloc[-1] if not swing_highs.empty else None
        last_swing_low = swing_lows['low'].iloc[-1] if not swing_lows.empty else None

        # 取前一个 swing 作为对侧流动性目标
        target_high = swing_highs['high'].iloc[-2] if len(swing_highs) >= 2 else None
        target_low = swing_lows['low'].iloc[-2] if len(swing_lows) >= 2 else None

        if signal == 1:  # 多头
            stop_loss = last_swing_high * 0.995
            entry_price = last_close
            risk = entry_price - stop_loss
            take_profit = target_high if target_high and target_high > entry_price else entry_price + 2 * risk

        elif signal == -1:  # 空头
            stop_loss = last_swing_low * 1.005
            entry_price = last_close
            risk = stop_loss - entry_price
            take_profit = target_low if target_low and target_low < entry_price else entry_price - 2 * risk

        else:
            return None

        # 如果 risk <= 0，直接过滤掉无效策略
        if risk <= 0:
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
