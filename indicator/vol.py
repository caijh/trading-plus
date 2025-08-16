from calculate.service import detect_turning_point_indexes
from indicator.base import Indicator


class VOL(Indicator):
    """
    通用成交量确认类。

    该类用于根据给定的参数判断股票的成交量是否符合特定的模式，以辅助投资决策。
    """

    def __init__(self, signal=1, mode='any', volume_window=20, stddev_mult=1.0):
        """
        初始化成交量确认对象。

        :param signal: 1 表示买入确认，-1 表示卖出确认
        :param mode: 模式，可选 ['heavy', 'light', 'turning_up', 'turning_down', 'any']
        :param volume_window: 均值/标准差计算的历史窗口
        :param stddev_mult: 用于识别放量/缩量的标准差倍数
        """
        self.signal = signal
        self.mode = mode
        self.volume_window = volume_window
        self.stddev_mult = stddev_mult
        self.label = f'VOL'
        self.weight = 1

    def match(self, stock, df, trending, direction):
        """
        根据成交量模式匹配股票。

        :param stock: 股票代码
        :param df: 包含成交量等信息的数据框
        :param trending 趋势
        :param direction 方向
        :return: 如果成交量模式匹配，则返回 True，否则返回 False
        """
        # 检查数据是否足够
        if df is None or len(df) < self.volume_window + 5:
            return False

        # 获取最新成交量
        latest_vol = df['volume'].iloc[-1]
        if latest_vol <= 0:
            return False

        # 计算最近的成交量均值和标准差
        recent_vol = df['volume'].iloc[-self.volume_window:]
        avg_vol = recent_vol.mean()
        std_vol = recent_vol.std()

        # 判断放量 / 缩量
        is_heavy_volume = latest_vol > (avg_vol + self.stddev_mult * std_vol)
        is_light_volume = latest_vol < (avg_vol - self.stddev_mult * std_vol)

        vol_sma = df['volume']

        # 检测成交量转折点
        turning_point_indexes, turning_up, turning_down = detect_turning_point_indexes(vol_sma)

        # 根据模式返回匹配结果
        if self.mode == 'heavy':
            return is_heavy_volume
        elif self.mode == 'light':
            return is_light_volume
        elif self.mode == 'turning_up':
            is_volume_turning = any(idx >= len(df) - 4 for idx in turning_up)
            return is_volume_turning
        elif self.mode == 'turning_down':
            is_volume_turning = any(idx >= len(df) - 4 for idx in turning_down)
            return is_volume_turning
        elif self.mode == 'any':
            price_sma = df['close']
            if self.signal == 1:
                same_trend = price_sma.iloc[-1] > price_sma.iloc[-2] and vol_sma.iloc[-1] > vol_sma.iloc[-2]
            else:
                same_trend = price_sma.iloc[-1] < price_sma.iloc[-2] and vol_sma.iloc[-1] < vol_sma.iloc[-2]
            return is_heavy_volume or is_light_volume or same_trend
        return False
