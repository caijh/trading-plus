import pandas_ta as ta

from indicator.base import Indicator


class AROON(Indicator):
    def __init__(self, signal=1, period=14):
        """
        初始化 Aroon 趋势确认指标

        参数:
        - signal: 1 表示确认多头趋势（Aroon Up 强），
                  -1 表示确认空头趋势（Aroon Down 强）
        - period: Aroon 计算周期
        """
        self.signal = signal
        self.period = period
        self.label = f'AROON{period}'
        self.weight = 1

    def match(self, stock, df, trending, direction, up_threshold=70, down_threshold=70):
        """
        判断是否符合趋势确认条件
        - 多头确认: Aroon Up >= up_threshold 且 Aroon Down <= (100 - up_threshold)
        - 空头确认: Aroon Down >= down_threshold 且 Aroon Up <= (100 - down_threshold)
        """
        if df is None or len(df) < self.period + 1:
            print(f'{stock["code"]} 数据不足，无法计算 Aroon 指标')
            return False

        # 计算 Aroon Up 和 Aroon Down
        aroon_df = ta.aroon(df['high'], df['low'], length=self.period)
        aroon_up = aroon_df.iloc[:, 0]
        aroon_down = aroon_df.iloc[:, 1]

        latest_up = aroon_up.iloc[-1]
        latest_down = aroon_down.iloc[-1]

        if self.signal == 1:  # 多头确认
            return latest_up >= up_threshold and latest_down <= (100 - up_threshold)

        elif self.signal == -1:  # 空头确认
            return latest_down >= down_threshold and latest_up <= (100 - down_threshold)

        return False
