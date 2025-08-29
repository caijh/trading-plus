import pandas_ta as ta

from indicator.base import Indicator
from indicator.volume_registry import volume_registry


class WR(Indicator):
    weight = 1
    signal = 1
    recent = 1
    name = 'WR'

    def __init__(self, signal=1, recent=3):
        """
        :param signal: 1 表示买入，-1 表示卖出
        :param recent: 最近 N 天内是否出现信号
        """
        self.signal = signal
        self.label = 'WR'
        self.recent = recent

    def match(self, stock, df, trending, direction):
        """
        判断是否满足 WR 指标的买入或卖出信号。
        :param stock: 股票信息字典
        :param df: DataFrame，必须包含 high、low、close
        :param trending 趋势
        :param direction 方向
        :return: True / False
        """
        # 计算 WR 指标，默认周期 14
        wr_df = ta.willr(high=df['high'], low=df['low'], close=df['close'], length=14)
        df[self.label] = wr_df

        if self.signal == 1:
            # 买入信号：WR 上穿 -80（从超卖区域反弹）
            df[f'{self.label}_Signal'] = (wr_df.shift(1) < -80) & (wr_df > wr_df.shift(1))
        elif self.signal == -1:
            # 卖出信号：WR 下穿 -20（从超买区域回落）
            df[f'{self.label}_Signal'] = (wr_df.shift(1) > -20) & (wr_df < wr_df.shift(1))
        else:
            return False

        # 最近 N 天是否出现信号
        recent_signals = df.tail(self.recent)
        signal = recent_signals[f'{self.label}_Signal'].any()

        return signal

    def get_volume_confirm_patterns(self):
        return volume_registry.get(self.name).get(self.signal)
