from calculate.service import get_total_volume_around, get_distance
from strategy.model import TradingStrategy
from strategy.trading_model import TradingModel


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

        if point_1['low'] < close < point_2['high'] and point_2['high'] > point_3['low'] and point_3['low'] < point_4[
            'high']:
            # 比较 point1 与 point3 处前后 3 天的成交量均值
            if get_total_volume_around(df, point_1.name, 3) < get_total_volume_around(df, point_3.name, 3):
                return 0
            return 1
        elif point_2['low'] < close < point_1['high'] and point_2['low'] < point_3['high'] and point_3['high'] > \
            point_4['low']:
            # 比较 point1 与 point3 处前后 5 天的成交量均值
            if get_total_volume_around(df, point_1.name, 3) < get_total_volume_around(df, point_3.name, 3):
                return 0
            return -1

        return 0

    def create_trading_strategy(self, stock, df, signal):
        last_close = df['close'].iloc[-1]
        n_digits = 3 if stock['stock_type'] == 'Fund' else 2
        turning_points = df[df['turning'] != 0]
        point_1 = turning_points.iloc[-1]
        point_2 = turning_points.iloc[-2]
        patterns = []
        if signal == 1:  # 多头
            stop_loss = point_1['low']
            entry_price = last_close * 0.998
            target_high = point_2['high']
            take_profit = target_high * 0.998
            patterns.extend(['N', 'UP'])
        elif signal == -1:  # 空头
            stop_loss = point_1['high']
            entry_price = last_close * 1.002
            target_low = point_2['low']
            take_profit = target_low * 1.002
            patterns.extend(['N', 'DOWN'])
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
