import pandas_ta as ta

from strategy.model import TradingStrategy
from strategy.trading_model import TradingModel


class AlBrooksProTradingModel(TradingModel):
    """
    Brooks-style trading model with:
    - EMA trend context
    - Multi-leg pullback detection (High2 / Low2) with dynamic N-leg scan
    - Trend Bar, Failed Breakout, Inside Bar
    - Dynamic optimal entry calculation
    """

    def __init__(self, pullback_lookback=3):
        super().__init__('AlBrooksProTradingModel')
        self.patterns = []
        self.pullback_lookback = pullback_lookback  # 最近N根K线扫描回撤
        self.optimal_entry = None

    def get_trading_signal(self, stock, df, trending=None, direction=None):
        if len(df) < self.pullback_lookback + 2:
            return 0, []

        self.patterns = []
        self.optimal_entry = None

        # --- EMA trend ---
        ema20_series = ta.ema(close=df['close'], length=20)
        ema20 = ema20_series.iloc[-1]
        prev_ema20 = ema20_series.iloc[-2]
        close = df['close'].iloc[-1]
        high = df['high'].iloc[-1]
        low = df['low'].iloc[-1]

        is_bull_trend = close > ema20 > prev_ema20
        is_bear_trend = close < ema20 < prev_ema20

        # --- Multi-leg pullback detection ---
        if is_bull_trend:
            # 扫描最近 N 根K线寻找两腿回撤
            lows = df['low'].iloc[-self.pullback_lookback:]
            highs = df['high'].iloc[-self.pullback_lookback:]
            closes = df['close'].iloc[-self.pullback_lookback:]

            first_leg_low = lows.iloc[0]
            second_leg_low = lows.iloc[1:].min()  # 第二腿最底点
            second_leg_idx = lows.iloc[1:].idxmin()
            if second_leg_low > first_leg_low:
                # 第二腿回撤浅
                leg_range = highs.iloc[0] - first_leg_low
                second_leg_depth = second_leg_low - first_leg_low
                if 0 < second_leg_depth / leg_range < 0.8:
                    self.patterns.append('high_2_bull_flag')
                    # 动态入场点：第二腿低点 + 小幅回升
                    self.optimal_entry = second_leg_low + 0.2 * leg_range

        if is_bear_trend:
            highs = df['high'].iloc[-self.pullback_lookback:]
            lows = df['low'].iloc[-self.pullback_lookback:]
            closes = df['close'].iloc[-self.pullback_lookback:]

            first_leg_high = highs.iloc[0]
            second_leg_high = highs.iloc[1:].max()
            second_leg_idx = highs.iloc[1:].idxmax()
            if second_leg_high < first_leg_high:
                leg_range = first_leg_high - lows.iloc[0]
                second_leg_depth = first_leg_high - second_leg_high
                if 0 < second_leg_depth / leg_range < 0.8:
                    self.patterns.append('low_2_bear_flag')
                    # 动态入场点：第二腿高点 - 小幅回落
                    self.optimal_entry = second_leg_high - 0.2 * leg_range

        # --- Trend Bar ---
        if is_bull_trend and close > df['close'].iloc[-2] and high > df['high'].iloc[-2] and low > df['low'].iloc[-2]:
            if close > (high + low) / 2:
                self.patterns.append('trend_bar_up')
        elif is_bear_trend and close < df['close'].iloc[-2] and high < df['high'].iloc[-2] and low < df['low'].iloc[-2]:
            if close < (high + low) / 2:
                self.patterns.append('trend_bar_down')

        # --- Failed Breakout ---
        if df['low'].iloc[-2] < df['low'].iloc[-3] and close > df['low'].iloc[-2] and is_bull_trend:
            self.patterns.append('failed_breakout_reversal_up')
        if df['high'].iloc[-2] > df['high'].iloc[-3] and close < df['high'].iloc[-2] and is_bear_trend:
            self.patterns.append('failed_breakout_reversal_down')

        # --- Inside Bar ---
        if high < df['high'].iloc[-2] and low > df['low'].iloc[-2]:
            if is_bull_trend and close > df['close'].iloc[-2]:
                self.patterns.append('inside_bar_bullish_continuation')
            elif is_bear_trend and close < df['close'].iloc[-2]:
                self.patterns.append('inside_bar_bearish_continuation')

        # --- Final Signal ---
        bullish_patterns = ['high_2_bull_flag', 'trend_bar_up', 'inside_bar_bullish_continuation',
                            'failed_breakout_reversal_up']
        bearish_patterns = ['low_2_bear_flag', 'trend_bar_down', 'inside_bar_bearish_continuation',
                            'failed_breakout_reversal_down']

        if any(p in bullish_patterns for p in self.patterns):
            return 1
        elif any(p in bearish_patterns for p in self.patterns):
            return -1
        else:
            return 0

    def create_trading_strategy(self, stock, df, signal):
        if signal == 0:
            return None

        n_digits = 3 if stock.get('stock_type', '') == 'Fund' else 2

        if hasattr(self, 'optimal_entry') and self.optimal_entry is not None:
            entry_price = round(self.optimal_entry, n_digits)
        else:
            # fallback to last close adjustment
            last_close = df['close'].iloc[-1]
            entry_price = round(last_close * (1.002 if signal == 1 else 0.998), n_digits)

        current_bar_low = df['low'].iloc[-1]
        current_bar_high = df['high'].iloc[-1]

        if signal == 1:
            stop_loss = round(current_bar_low, n_digits)
            take_profit = round(entry_price + (entry_price - stop_loss) * 2, n_digits)
        else:
            stop_loss = round(current_bar_high, n_digits)
            take_profit = round(entry_price - (stop_loss - entry_price) * 2, n_digits)

        if abs(entry_price - stop_loss) <= 0:
            return None

        strategy = TradingStrategy(
            strategy_name=self.name,
            stock_code=stock['code'],
            stock_name=stock['name'],
            entry_patterns=self.patterns.copy(),
            exit_patterns=[],
            exchange=stock['exchange'],
            entry_price=entry_price,
            take_profit=take_profit,
            stop_loss=stop_loss,
            signal=signal
        )
        return strategy
