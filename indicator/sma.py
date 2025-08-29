import pandas_ta as ta

from indicator.base import Indicator
from indicator.ma_volume_registry import volume_registry


class SMA(Indicator):
    """
    简单移动平均线（SMA）信号判断类。

    该类用于判断股票价格与简单移动平均线（SMA）之间的金叉或死叉信号，
    并结合指数移动平均线（EMA）进行确认。

    属性:
        ma (int): 移动平均线的计算周期。
        label (str): 移动平均线的标签名称，格式为 'SMA{ma}'。
        signal (int): 信号类型，1 表示金叉信号，-1 表示死叉信号。
        weight (int): 信号权重，默认为 1。
        name (str): 指标名称，固定为 'SMA'。
    """
    ma = 5
    label = ''
    signal = 1
    weight = 1
    name = 'SMA'

    def __init__(self, ma, signal):
        """
        初始化 SMA 类实例。

        参数:
            ma (int): 移动平均线的计算周期。
            signal (int): 信号类型，1 表示金叉信号，-1 表示死叉信号。
        """
        self.ma = ma
        self.signal = signal
        self.label = f'SMA{self.ma}'

    def match(self, stock, df, trending, direction):
        """
        判断股票价格MA是否发生金叉或死叉。

        参数:
            stock: 字典，包含股票信息。
            df: DataFrame，包含股票的DataFrame数据，至少包含['close']列。

        返回:
            布尔值，如果发生金叉或死叉，则返回True，否则返回False。
        """
        # 数据长度不足时无法计算均线，直接返回False
        if len(df) < self.ma:
            return False

        # 获取最新价格数据
        price = df.iloc[-1]

        # 计算指定周期的简单移动平均线
        if f'{self.label}' not in df.columns:
            df[f'{self.label}'] = ta.sma(df['close'], self.ma).round(3)
        ma = df[f'{self.label}']
        # 获取最新和前一均线价格，用于比较
        latest_ma_price = ma.iloc[-1]
        pre_ma_price = ma.iloc[-2]

        # 计算收盘价的5日指数移动平均(EMA)
        if 'EMA5' not in df.columns:
            ema = ta.ema(df['close'], 5).round(3)
        else:
            ema = df['EMA5']
        latest_ema_price = ema.iloc[-1]
        pre_ema_price = ema.iloc[-2]
        close_price = price['close']

        # 根据信号类型判断金叉或死叉条件
        if self.signal == 1:
            # 金叉条件：收盘价上穿EMA，且EMA上穿SMA
            return ((latest_ema_price > latest_ma_price) and (pre_ema_price < pre_ma_price)
                    and (close_price >= latest_ema_price))
        elif self.signal == -1:
            # 死叉条件：收盘价下穿EMA，且EMA下穿SMA
            return ((latest_ema_price < latest_ma_price) and (pre_ema_price > pre_ma_price)
                    and (close_price <= latest_ema_price))
        return False

    def get_volume_confirm_patterns(self):
        """
        获取与当前 SMA 信号相关的成交量确认模式。

        返回:
            list: 与当前 SMA 信号类型对应的成交量确认模式列表。
        """
        return volume_registry.get(self.name).get(self.signal)
