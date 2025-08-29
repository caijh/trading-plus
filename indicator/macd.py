import pandas_ta as ta

from indicator.base import Indicator
from indicator.volume_registry import volume_registry


class MACD(Indicator):
    """
    MACD指标类，用于判断股票的买入或卖出信号（金叉/死叉）。

    Attributes:
        label (str): 指标名称标签，默认为空字符串。
        signal (int): 信号类型，1表示买入信号（金叉），-1表示卖出信号（死叉）。
        weight (int): 指标权重，默认为1。
        recent (int): 判断最近几根K线的交叉情况，默认为3。
        name (str): 指标名称，固定为'MACD'。
    """

    label = ''
    signal = 1
    weight = 1
    recent = 3
    name = 'MACD'

    def __init__(self, signal, recent=3):
        """
        初始化MACD指标实例。

        Args:
            signal (int): 信号类型，1表示买入信号（金叉），-1表示卖出信号（死叉）。
            recent (int, optional): 判断最近几根K线的交叉情况。默认为3。
        """
        self.label = 'MACD'
        self.signal = signal
        self.recent = recent

    def match(self, stock, df, trending, direction):
        """
        根据给定的股票数据判断是否满足MACD金叉或死叉条件。

        Args:
            stock (str): 股票代码（未使用，保留接口兼容性）。
            df (pd.DataFrame): 包含股票历史价格的数据框，需包含'close'列
            trending: 趋势
            direction: 方向

        Returns:
            bool: 如果满足信号条件返回True，否则返回False。
        """
        if len(df) < 60:
            return False

        # 计算MACD指标并重命名列
        macd_df = ta.macd(df['close'])
        macd_df.rename(columns={
            'MACD_12_26_9': 'DIF',
            'MACDs_12_26_9': 'DEA',
            'MACDh_12_26_9': 'Histogram'
        }, inplace=True)

        dif = macd_df['DIF'].dropna()
        dea = macd_df['DEA'].dropna()

        if len(dif) < self.recent + 1:
            return False

        # 获取最近若干根K线的DIF和DEA值
        recent_dif = dif.iloc[-self.recent:]
        recent_dea = dea.iloc[-self.recent:]

        if self.signal == 1:  # 买入信号（金叉）
            # 条件：最新一根 DIF 上穿 DEA
            if recent_dif.iloc[-2] <= recent_dea.iloc[-2] and recent_dif.iloc[-1] > recent_dea.iloc[-1]:
                return True

        elif self.signal == -1:  # 卖出信号（死叉）
            # 条件：最新一根 DIF 下穿 DEA
            if recent_dif.iloc[-2] >= recent_dea.iloc[-2] and recent_dif.iloc[-1] < recent_dea.iloc[-1]:
                return True

        return False

    def get_volume_confirm_patterns(self):
        """
        获取与当前MACD信号对应的成交量确认模式。

        Returns:
            list or None: 成交量确认模式列表，如果没有匹配项则返回None。
        """
        return volume_registry.get(self.name).get(self.signal)
