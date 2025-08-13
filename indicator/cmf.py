import pandas_ta as ta


class CMF:
    def __init__(self, signal=1, period=20):
        """
        初始化 Chaikin Money Flow（CMF）策略

        参数:
        - signal: 1 表示买入信号（CMF 上升或为正），-1 表示卖出信号（CMF 下降或为负）
        - period: CMF 计算周期，默认为 20
        """
        self.signal = signal
        self.period = period
        self.label = f'CMF{period}'
        self.weight = 1

    def match(self, stock, prices, df):
        if df is None or len(df) < self.period + 2:
            print(f'{stock["code"]} 数据不足，无法计算 CMF 指标')
            return False

        # 获取最新价格信息
        price = df.iloc[-1]
        # 将最新成交量转换为浮点数
        latest_volume = float(price['volume'])
        # 如果最新成交量不大于0，则不进行后续判断
        if not latest_volume > 0:
            return False

        # 计算 CMF
        cmf = ta.cmf(df['high'], df['low'], df['close'], df['volume'], length=self.period)
        latest = cmf.iloc[-1]
        prev = cmf.iloc[-3]

        # 买入信号：CMF 上升且为正
        if self.signal == 1:
            # 连续上升 + 当前为正 + 高于中性带
            return latest > prev and latest > 0

        # 卖出信号：CMF 下降且为负
        elif self.signal == -1:
            # 连续下降 + 当前为负 + 低于中性带
            return latest < prev and latest < 0

        else:
            raise False
