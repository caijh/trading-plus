class VPT:
    """
    VPT 指标计算类。

    Attributes:
        signal (int): 信号类型，1 表示买入信号，-1 表示卖出信号。
        label (str): 标识字符串，用于标识 VPT 和周期。
        weight (int): 权重，默认为 1。
    """

    def __init__(self, signal=1):
        """
        初始化 VPT 实例。

        Args:
            signal (int, optional): 信号类型，默认为 1（买入信号）。
        """
        self.signal = signal
        self.label = f'VPT'
        self.weight = 1

    def match(self, stock, df):
        """
        判断当前数据是否满足 VPT 信号条件。

        Args:
            stock (dict): 股票信息字典。
            df (pd.DataFrame): 包含股票数据的 DataFrame，包括 'close' 和 'volume' 列。

        Returns:
            bool: 如果满足信号条件返回 True，否则返回 False。
        """
        # 检查数据长度是否足够计算 VPT
        if df is None or len(df) < 5:
            print(f'{stock["code"]} 数据不足，无法计算 VPT')
            return False
        # 检查最新成交量是否有效
        if df['volume'].iloc[-1] <= 0:
            return False
        # 计算 VPT 值
        vpt = (df['close'].pct_change().fillna(0) * df['volume']).cumsum()
        # 获取最近的 VPT 值
        latest = vpt.iloc[-1]
        prev = vpt.iloc[-2]
        # 根据信号类型判断是否满足条件
        if self.signal == 1:
            return latest > prev > 0
        elif self.signal == -1:
            return latest < prev
        return False
