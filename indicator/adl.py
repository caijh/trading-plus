import pandas_ta as ta

from calculate.service import upping_trending, downing_trending


class ADL:
    """
    ADLine 类用于计算和匹配股票的 ADLine（累积/派发线）指标。

    属性:
    - signal (int): 信号类型，1 表示买入信号，-1 表示卖出信号。
    - label (str): 标识 ADLine 的标签。
    - weight (int): 信号的权重。
    """

    def __init__(self, signal=1, window=3):
        """
        初始化 ADLine 类。

        参数:
        - signal (int): 默认为 1，表示默认信号为买入信号。
        """
        self.signal = signal
        self.label = 'ADL'
        self.weight = 1
        self.window = window

    def match(self, stock, prices, df):
        """
        匹配给定股票的 ADLine 信号。

        参数:
        - stock (dict): 包含股票信息的字典。
        - prices (list): 未使用，保留参数，可为价格列表。
        - df (DataFrame): 包含股票数据的 DataFrame，用于计算 ADLine。

        返回:
        - bool: 如果匹配到指定的 ADLine 信号，则返回 True，否则返回 False。
        """
        # 检查数据是否足够计算 ADLine
        if df is None or len(df) < 3:
            print(f'{stock["code"]} 数据不足，无法计算 ADLine')
            return False

        # 获取最新价格数据
        price = df.iloc[-1]
        latest_volume = float(price['volume'])

        # 确保最新成交量大于 0，否则返回 False
        if not latest_volume > 0:
            return False

        # 计算 ADLine
        ad_line = ta.ad(df['high'], df['low'], df['close'], df['volume'])

        if self.signal == 1:
            return upping_trending(ad_line)
        elif self.signal == -1:
            return downing_trending(ad_line)
        return False
