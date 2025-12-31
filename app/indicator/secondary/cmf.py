import pandas as pd
import pandas_ta as ta

from app.indicator.base import Indicator


class CMF(Indicator):
    """
    一个基于 Chaikin Money Flow (CMF) 指标的交易策略类。
    参数:
    - signal (int): 1 表示买入信号，-1 表示卖出信号。
    - period (int): CMF 指标的计算周期，默认为 20。
    """

    def __init__(self, signal, period: int = 20):
        self.signal = signal
        self.period = period
        self.label = f'CMF{period}'
        self.weight = 1

    def match(self, stock: dict, df: pd.DataFrame, trending, direction) -> bool:
        """
        检查给定股票数据是否匹配策略设定的交易信号。

        参数:
        - stock (dict): 包含股票信息的字典。
        - df (pd.DataFrame): 包含 OHLCV (开盘价、最高价、最低价、收盘价、成交量) 数据的 DataFrame。

        返回:
        - bool: 如果匹配交易信号则返回 True，否则返回 False。
        """
        # 确保数据量足够计算 CMF
        if df is None or len(df) < self.period + 1:
            print(f'{stock.get("code", "未知")} 数据不足，无法计算 CMF 指标')
            return False

        # 使用 pandas_ta 计算 CMF
        cmf_series = ta.cmf(df['high'], df['low'], df['close'], df['volume'], length=self.period)

        # 确保计算结果非空
        if cmf_series.empty or len(cmf_series) < 2:
            return False

        current_cmf = cmf_series.iloc[-1]
        previous_cmf = cmf_series.iloc[-2]

        if self.signal == 1:
            # 买入信号：中线穿越信号
            # 买入信号：CMF 持续上升且处于正值区域
            return (previous_cmf < 0 < current_cmf) or (current_cmf > previous_cmf and current_cmf > 0)

        elif self.signal == -1:
            # 卖出信号：CMF 从正值区域穿越到负值区域
            # 卖出信号：CMF 持续下降且处于负值区域
            return (previous_cmf > 0 > current_cmf) or (current_cmf < previous_cmf and current_cmf < 0)

        return False
