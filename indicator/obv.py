import pandas_ta as ta

from calculate.service import upping_trending, downing_trending
from indicator.base import Indicator


class OBV(Indicator):

    def __init__(self, signal):
        """
        初始化OBV对象。

        参数:
        - signal: 指示信号类型，1代表买入信号，其他值代表卖出信号。
        """
        self.signal = signal
        self.label = 'OBV'
        self.weight = 1

    def match(self, stock, df, trending, direction):
        """
        根据给定的数据判断是否满足OBV买入或卖出信号。

        参数:
        - stock: 股票信息，未在本函数中使用。
        - prices: 价格信息，未在本函数中使用。
        - df: 包含股票数据的DataFrame，包括['close'（收盘价）和 'volume'（成交量）]列。

        返回:
        - 如果满足买入或卖出信号则返回True，否则返回False。
        """
        # 获取最新价格信息
        price = df.iloc[-1]
        # 提取最新成交量并检查是否为正值
        latest_volume = float(price['volume'])
        if not latest_volume > 0:
            # 如果成交量为负，则不进行后续判断，返回False
            return False

        # 计算 OBV 指标
        obv = ta.obv(df['close'], df['volume'])
        # 判断买入信号
        if self.signal == 1:
            return upping_trending(obv)
        elif self.signal == -1:
            return downing_trending(obv)
        return False
