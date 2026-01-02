import pandas_ta as ta

from app.indicator.base import Indicator


class ADOSC(Indicator):
    label = ''
    signal = 1
    weight = 1

    def __init__(self, signal, threshold=5000):
        self.signal = signal
        self.label = 'ADOSC'
        self.threshold = threshold

    def match(self, stock, df, trending, direction):
        """
        判断给定股票是否满足特定的交易条件。

        通过计算股票的最新价格和成交量，以及使用累积/派发指标(ADOSC)来评估股票的买卖压力，
        进而判断股票是否处于一个可能的买入或卖出状态。

        参数:
        - stock: 股票标识符，用于识别特定的股票。
        - prices: 包含股票历史价格的列表，每个元素是一个字典，至少包含close和volume字段。
        - df: 包含股票价格和成交量的数据框，用于计算ADOSC指标。

        返回:
        - 如果股票满足特定的交易条件则返回True，否则返回False。
        """
        # 获取最新价格信息
        price = df.iloc[-1]
        # 将最新成交量转换为浮点数
        latest_volume = float(price['volume'])
        # 如果最新成交量不大于0，则不进行后续判断
        if not latest_volume > 0:
            return False

        # 计算 ADOSC 指标
        adosc = ta.adosc(df['high'], df['low'], df['close'], df['volume'])
        if adosc is None or adosc.empty:
            return False
        latest = adosc.iloc[-1]
        prev = adosc.iloc[-2]

        if self.signal == 1:
            return latest > prev
        elif self.signal == -1:
            return latest < prev
        return False
