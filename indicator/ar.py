class AR:
    name = 'AR'

    def __init__(self, signal=1, period=26, threshold=100):
        """
        AR 人气指标策略

        参数:
        - signal: 1 表示买入信号（AR 大于阈值），-1 表示卖出信号（AR 小于阈值）
        - period: AR 计算周期，默认 26
        - threshold: AR 指标阈值，通常 100
        """
        self.signal = signal
        self.period = period
        self.threshold = threshold
        self.label = f'AR{period}'
        self.weight = 1

    def calculate_ar(self, df):
        # 高开差与开低差
        high_open = df['high'] - df['open']
        open_low = df['open'] - df['low']

        ar = high_open.rolling(self.period).sum() / open_low.rolling(self.period).sum() * 100
        return ar

    def match(self, stock, df):
        """
        确认主指标有效性
        返回 True 表示主指标有效，False 表示无效
        """
        if 'high' not in df or 'low' not in df or 'open' not in df:
            return False

        df[self.label] = self.calculate_ar(df)
        ar_value = df[self.label].iloc[-1]

        if self.signal == 1:
            return ar_value > self.threshold
        elif self.signal == -1:
            return ar_value < self.threshold
        return False
