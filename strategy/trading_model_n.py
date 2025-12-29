import pandas_ta as ta

from calculate.service import get_distance, get_total_volume_around
from indicator.primary.rsi import RSI
from indicator.primary.wr import WR
from indicator.secondary.obv import OBV
from stock.constant import Trend
from strategy.model import TradingStrategy
from strategy.trading_model import TradingModel


def confirm_trend(stock, df, trending, direction, signal):
    if (
        (WR(signal).match(stock, df, trending, direction) or RSI(signal).match(stock, df, trending, direction))
        and OBV(signal).match(stock, df, trending, direction)
    ):
        if signal == 1:
            return Trend.UP
        elif signal == -1:
            return Trend.DOWN
    return Trend.UNKNOWN


class NTradingModel(TradingModel):
    def __init__(self):
        """
        初始化交易模型。
        """
        super().__init__('NTradingModel')

    def get_trading_signal(self, stock, df, trending, direction):
        turning_points = df[df['turning'] != 0]
        if len(turning_points) < 4:
            return 0
        point_1 = turning_points.iloc[-1]
        point_2 = turning_points.iloc[-2]
        point_3 = turning_points.iloc[-3]
        point = df.iloc[-1]
        close = point['close']
        if get_distance(df, point, point_1) > 3:
            return 0
        signal = 0

        volume_point3 = get_total_volume_around(df, point_3.name, 2)
        volume_cur = get_total_volume_around(df, point_1.name, 2)
        # 最一个拐点前是上涨N
        if (point_3['low'] < point_1['low'] < close < point_2['high']
            and point_2['high'] > point_3['low']
            and point_1['low'] < (point_3['low'] + (point_2['high'] - point_3['low']) * 0.382)
            and point_1['turning'] == 1
            and volume_cur > volume_point3
        ):
            signal = 1
        # 最后一个拐点前是下跌N
        elif (point_2['low'] < close < point_1['high'] < point_3['high']
              and point_3['high'] > point_2['low']
              and point_1['high'] > (point_3['high'] - (point_3['high'] - point_2['low']) * 0.382)
              and point_1['turning'] == -1
              and volume_cur > volume_point3
        ):
            signal = -1

        # ---- 趋势指标确认 ----
        if (signal == 1
            and confirm_trend(stock, df, trending, direction, signal) != Trend.UP
        ):
            return 0
        if (signal == -1
            and confirm_trend(stock, df, trending, direction, signal) != Trend.DOWN
        ):
            return 0

        return signal

    def create_trading_strategy(self, stock, df, signal):
        last_close = df['close'].iloc[-1]
        n_digits = 3 if stock['stock_type'] == 'Fund' else 2
        turning_points = df[df['turning'] != 0]
        point_1 = turning_points.iloc[-1]
        point_2 = turning_points.iloc[-2]

        # 计算 ATR (真实波动率)
        atr_series = ta.atr(df['high'], df['low'], df['close'], length=14)  # 假设 ATR 计算函数返回的是一个包含 ATR 值的 Series
        atr_value = atr_series.iloc[df.index.get_loc(point_1.name)]
        patterns = []
        if signal == 1:  # 多头信号
            # 根据 ATR 调整 entry_price, stop_loss, take_profit
            stop_loss = point_1['low'] - atr_value * 0.5  # 止损基于低点，加入 ATR 增加灵活性
            entry_price = last_close * 0.998  # 入场价格略低于当前收盘价
            target_high = point_2['high']
            take_profit = target_high - atr_value * 0.5  # 止盈价格加入 ATR 调整

            patterns.extend(['N', 'UP', 'WR', 'PVI'])

        elif signal == -1:  # 空头信号
            # 根据 ATR 调整 entry_price, stop_loss, take_profit
            stop_loss = point_1['high'] + atr_value * 0.5  # 止损基于高点，加入 ATR 增加灵活性
            entry_price = last_close * 1.002  # 入场价格略高于当前收盘价
            target_low = point_2['low']
            take_profit = target_low + atr_value * 0.5  # 止盈价格加入 ATR 调整

            patterns.extend(['N', 'DOWN', 'WR', 'PVI'])

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
            entry_patterns=patterns,
            exit_patterns=[],
            exchange=stock['exchange'],
            entry_price=float(round(entry_price, n_digits)),
            take_profit=float(round(take_profit, n_digits)),
            stop_loss=float(round(stop_loss, n_digits)),
            signal=signal
        )
        return strategy
