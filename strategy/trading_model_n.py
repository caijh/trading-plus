from calculate.service import get_distance, get_total_volume_around
from indicator.pvi import PVI
from indicator.rsi import RSI
from indicator.wr import WR
from stock.constant import Trend
from strategy.model import TradingStrategy
from strategy.trading_model import TradingModel


def confirm_trend(stock, df, trending, direction, signal):
    if (
        (WR(signal).match(stock, df, trending, direction) or RSI(signal).match(stock, df, trending, direction))
        and PVI(signal).match(stock, df, trending, direction)
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
        point_4 = turning_points.iloc[-4]
        point = df.iloc[-1]
        close = point['close']
        if get_distance(df, point_1, point) > 3:
            return 0
        signal = 0

        volume_point3 = get_total_volume_around(df, point_3.name, 3)
        volume_point4 = get_total_volume_around(df, point_4.name, 3)
        volume_cur = get_total_volume_around(df, point_1.name, 3)
        # 最一个拐点前是上涨N
        if (point_3['low'] < point_1['low'] < close < point_2['high']
            and point_3['low'] < point_4['high']
            and point_1['low'] < (point_4['high'] + point_2['high']) / 2
            and point_1['turning'] == 1
            and volume_cur < volume_point4
        ):
            signal = 1
        # 最后一个拐点前是下跌N
        elif (point_2['low'] < close < point_1['high'] < point_3['high']
              and point_3['high'] > point_4['low']
              and point_1['high'] > (point_4['low'] + point_3['high']) / 2
              and point_1['turning'] == -1
              and volume_cur < volume_point3
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
        patterns = []
        if signal == 1:  # 多头
            stop_loss = point_1['low']
            entry_price = last_close * 0.995
            target_high = point_2['high']
            take_profit = target_high * 0.995
            patterns.extend(['N', 'UP', 'WR', 'PVI'])
        elif signal == -1:  # 空头
            stop_loss = point_1['high']
            entry_price = last_close * 1.005
            target_low = point_2['low']
            take_profit = target_low * 1.005
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
