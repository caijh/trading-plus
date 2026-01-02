import pandas_ta as ta

from app.core.logger import logger
from app.indicator.base import Indicator


class MFI(Indicator):
    def __init__(self, signal=1, period=14):
        """
        初始化 Money Flow Index（MFI）策略

        参数:
        - signal: 1 表示买入信号（MFI 上升并脱离超卖区），-1 表示卖出信号（MFI 下降并脱离超买区）
        - period: MFI 计算周期，默认为 14
        """
        self.signal = signal
        self.period = period
        self.label = f'MFI{period}'
        self.weight = 1

    def match(self, stock, df, trending, direction, overbought=80, oversold=20):
        if df is None or len(df) < self.period + 3:
            logger.info(f'{stock["code"]} 数据不足，无法计算 MFI 指标')
            return False

        # 获取最新价格信息
        price = df.iloc[-1]
        latest_volume = float(price['volume'])
        if not latest_volume > 0:
            return False

        # 计算 MFI 指标
        mfi = ta.mfi(df['high'], df['low'], df['close'], df['volume'], length=self.period)
        latest = mfi.iloc[-1]
        prev = mfi.iloc[-2]

        if self.signal == 1:
            return prev < latest < oversold

        elif self.signal == -1:
            return prev > latest > latest > overbought

        return False
