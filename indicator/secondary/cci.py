from indicator.base import Indicator


class CCI(Indicator):
    signal = 1  # 1 表示买入信号，-1 表示卖出信号
    weight = 1
    period = 20
    name = 'CCI'

    def __init__(self, signal, period=20, recent=3):
        self.signal = signal
        self.label = "CCI"
        self.period = period
        self.recent = recent

    def match(self, stock, df, trending, direction):
        """
        判断CCI指标的买卖信号。

        :param stock: 股票信息字典，包含股票代码等信息。
        :param df: 股票历史数据 DataFrame，必须至少包含 ['high', 'low', 'close'] 列
        :param trending 趋势
        :param direction 方向

        :return: True/False，是否出现符合条件的买卖信号。
        """
        # 计算 CCI 指标（通常使用 20 天周期）
        df[f'{self.label}'] = df.ta.cci(length=self.period)

        # 确保 CCI 计算不为空
        if df[f'{self.label}'].isnull().all():
            print(f"CCI 计算失败，数据为空: {stock['code']}")
            return False

        cci_df = df[f'{self.label}']
        # 识别交易信号
        if self.signal == 1:
            # 买入信号：CCI 从低于 -100 反弹
            df[f'{self.label}_Signal'] = (cci_df.shift(1) < -100) & (cci_df > -100)
        else:
            # 卖出信号：CCI 从高于 100 回落
            df[f'{self.label}_Signal'] = (cci_df.shift(1) > 100) & (cci_df < 100)

        # 获取最近几天的数据
        recent_signals = df.tail(self.recent)

        # 判断是否出现信号
        signal = recent_signals[f'{self.label}_Signal'].any()

        return signal
