import pandas as pd
import pandas_ta as ta

from calculate.service import detect_turning_point_indexes, upping_trending, downing_trending
from indicator.adl import ADL
from indicator.cmf import CMF
from indicator.mfi import MFI
from indicator.obv import OBV


class VOL:
    """
    通用成交量确认类。

    该类用于根据给定的参数判断股票的成交量是否符合特定的模式，以辅助投资决策。
    """

    def __init__(self, signal=1, mode='any', volume_window=20, stddev_mult=1.0):
        """
        初始化成交量确认对象。

        :param signal: 1 表示买入确认，-1 表示卖出确认
        :param mode: 模式，可选 ['heavy', 'light', 'turning_up', 'turning_down', 'any']
        :param volume_window: 均值/标准差计算的历史窗口
        :param stddev_mult: 用于识别放量/缩量的标准差倍数
        """
        self.signal = signal
        self.mode = mode
        self.volume_window = volume_window
        self.stddev_mult = stddev_mult
        self.label = f'VOL'
        self.weight = 1

    def match(self, stock, df):
        """
        根据成交量模式匹配股票。

        :param stock: 股票代码
        :param prices: 价格数据（未使用）
        :param df: 包含成交量等信息的数据框
        :return: 如果成交量模式匹配，则返回 True，否则返回 False
        """
        # 检查数据是否足够
        if df is None or len(df) < self.volume_window + 5:
            return False

        # 获取最新成交量
        latest_vol = df['volume'].iloc[-1]
        if latest_vol <= 0:
            return False

        # 计算最近的成交量均值和标准差
        recent_vol = df['volume'].iloc[-self.volume_window:]
        avg_vol = recent_vol.mean()
        std_vol = recent_vol.std()

        # 判断放量 / 缩量
        is_heavy_volume = latest_vol > (avg_vol + self.stddev_mult * std_vol)
        is_light_volume = latest_vol < (avg_vol - self.stddev_mult * std_vol)

        vol_sma = df['volume']

        # 检测成交量转折点
        turning_point_indexes, turning_up, turning_down = detect_turning_point_indexes(vol_sma)

        # 根据模式返回匹配结果
        if self.mode == 'heavy':
            return is_heavy_volume
        elif self.mode == 'light':
            return is_light_volume
        elif self.mode == 'turning_up':
            is_volume_turning = any(idx >= len(df) - 4 for idx in turning_up)
            return is_volume_turning
        elif self.mode == 'turning_down':
            is_volume_turning = any(idx >= len(df) - 4 for idx in turning_down)
            return is_volume_turning
        elif self.mode == 'any':
            price_sma = df['close']
            if self.signal == 1:
                same_trend = price_sma.iloc[-1] > price_sma.iloc[-2] and vol_sma.iloc[-1] > vol_sma.iloc[-2]
            else:
                same_trend = price_sma.iloc[-1] < price_sma.iloc[-2] and vol_sma.iloc[-1] < vol_sma.iloc[-2]
            return is_heavy_volume or is_light_volume or same_trend
        return False


class ADOSC:
    label = ''
    signal = 1
    weight = 1

    def __init__(self, signal, threshold=5000):
        self.signal = signal
        self.label = 'ADOSC'
        self.threshold = threshold

    def match(self, stock, df):
        """
        判断给定股票是否满足特定的交易条件。

        通过计算股票的最新价格和成交量，以及使用累积/派发指标(ADOSC)来评估股票的买卖压力，
        进而判断股票是否处于一个可能的买入或卖出状态。

        参数:
        - stock: 股票标识符，用于识别特定的股票。
        - prices: 包含股票历史价格的列表，每个元素是一个字典，至少包含close和volume字段。
        - df: 包含股票价格和成交量的数据框，用于计算ADOSC指标。

        返回:
        - 如果股票满足特定的交易条件则返回True，否则返回False。
        """
        # 获取最新价格信息
        price = df.iloc[-1]
        # 将最新成交量转换为浮点数
        latest_volume = float(price['volume'])
        # 如果最新成交量不大于0，则不进行后续判断
        if not latest_volume > 0:
            return False

        # 计算 ADOSC 指标
        adosc = ta.adosc(df['high'], df['low'], df['close'], df['volume'])

        if self.signal == 1:
            return upping_trending(adosc)
        elif self.signal == -1:
            return downing_trending(adosc)
        return False


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


def get_breakthrough_up_volume_pattern():
    return [VOL(1), OBV(1), ADL(1), CMF(1), MFI(1), VPT(1)]


def get_breakthrough_down_volume_pattern():
    return [VOL(1), OBV(-1), ADL(-1), CMF(-1), MFI(-1), VPT(-1)]


def get_oversold_volume_patterns():
    return [VOL(-1), OBV(1), ADL(1), ADOSC(1), CMF(1), MFI(1), VPT(1)]


def get_overbought_volume_patterns():
    return [VOL(1), OBV(-1), ADL(-1), ADOSC(-1), CMF(-1), MFI(-1), VPT(-1)]
