import pandas_ta as ta

from indicator.base import Indicator


class BIAS(Indicator):
    ma = 5
    bias = -0.15
    label = ''
    signal = 1
    weight = 1
    name = 'BIAS'

    def __init__(self, ma, bias, signal):
        self.signal = signal
        self.ma = ma
        self.bias = bias
        self.label = f'Bias{self.ma}'

    def match(self, stock, df, trending, direction):
        """
        判断给定股票是否满足特定的买入条件。

        本函数使用偏差率指标来评估股票的当前价格是否被低估。
        参数:
        - stock: 股票对象，可能包含股票的基本信息（未在本函数中使用）。
        - prices: 股票价格数据（未在本函数中使用，可能为未来扩展保留）。
        - df: 包含股票历史数据的DataFrame，必须至少包含['close']列，代表收盘价。

        返回:
        - True：如果股票满足买入条件，即最新收盘价的偏差率小于0且小于预设的偏差阈值。
        - False：否则。
        """
        # 计算股票收盘价的偏差率
        if df is None or len(df) < self.ma:
            return False

        df[f'{self.label}'] = ta.bias(df['close'], self.ma)
        bias = df[f'{self.label}']
        # 获取最新的偏差率值
        latest_bias = bias.iloc[-1]
        if self.signal == 1:
            # 下跌，达到偏差值
            return latest_bias < self.bias
        else:
            # 上涨，达到偏差值
            return latest_bias > self.bias
