from indicator.base import Indicator


class AR(Indicator):
    name = 'AR'

    def __init__(self, signal, period=26, buy_threshold=50, sell_threshold=150):
        """
        AR 人气指标策略

        参数:
        - period: AR 计算周期，默认 26
        - buy_threshold: AR 指标买入阈值（超卖），通常为 50
        - sell_threshold: AR 指标卖出阈值（超买），通常为 150
        """
        self.signal = signal
        self.period = period
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.label = f'AR{period}'
        self.weight = 1

    def calculate_ar(self, df):
        """
        计算 AR 指标值
        """
        # 检查所需列是否存在
        required_columns = ['high', 'low', 'open']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"数据帧中缺少必需的列：{required_columns}")

        # 高开差与开低差
        high_open = df['high'] - df['open']
        open_low = df['open'] - df['low']

        # 避免除以零错误
        sum_open_low = open_low.rolling(self.period).sum()
        sum_open_low.loc[sum_open_low == 0] = 1e-9  # 将分母为0的值替换为一个极小值

        ar = high_open.rolling(self.period).sum() / sum_open_low * 100

        # 将计算结果添加到数据帧中
        df[self.label] = ar
        return df

    def match(self, stock, df, trending, direction):
        """
        根据 AR 指标判断交易信号

        返回:
        - 'buy': AR 值低于买入阈值
        - 'sell': AR 值高于卖出阈值
        - 'hold': 无信号
        """
        try:
            # 确保 AR 指标已计算
            if self.label not in df.columns:
                df = self.calculate_ar(df)

            ar_value = df[self.label].iloc[-1]
            if self.signal == 1:
                # 超卖，产生买入信号
                if ar_value < self.buy_threshold:
                    return True
            elif self.signal == -1:
                # 超买，产生卖出信号
                if ar_value > self.sell_threshold:
                    return True
            else:
                return False
        except Exception as e:
            print(f"匹配信号时发生错误: {e}")
            return False
