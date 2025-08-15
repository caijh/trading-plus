import pandas_ta as ta


class ADX:
    name = 'ADX'

    def __init__(self, signal=1, period=14, adx_threshold=25):
        """
        DMI 策略（+DI/-DI 交叉，趋势方向判断）

        参数:
        - signal: 1 表示买入信号（+DI 上穿 -DI），-1 表示卖出信号（-DI 上穿 +DI）
        - period: 计算周期
        - adx_threshold: 趋势强度过滤阈值
        """
        self.signal = signal
        self.period = period
        self.adx_threshold = adx_threshold
        self.label = f'ADX{period}'
        self.weight = 1

    def match(self, stock, df):
        if df is None or len(df) < self.period + 2:
            print(f'{stock["code"]} 数据不足，无法计算 DMI')
            return False

        # 使用 ta.adx 计算 +DI, -DI 和 ADX
        dmi = ta.adx(df['high'], df['low'], df['close'], length=self.period)
        if dmi is None or dmi.isnull().values.any():
            return False

        plus_di = dmi[f'DMP_{self.period}']
        minus_di = dmi[f'DMN_{self.period}']
        adx = dmi[f'ADX_{self.period}']

        # 最近两个周期的 DI 值
        latest_plus_di = plus_di.iloc[-1]
        latest_minus_di = minus_di.iloc[-1]
        adx_now = adx.iloc[-1]

        # 趋势强度判断
        if adx_now < self.adx_threshold:
            return False

        if self.signal == 1:
            return latest_plus_di > latest_minus_di
        elif self.signal == -1:
            return latest_plus_di < latest_minus_di
        return False
