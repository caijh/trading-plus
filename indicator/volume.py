import numpy as np
import pandas as pd
import pandas_ta as ta
from scipy.signal import argrelextrema


class VOL:
    """
    通用成交量确认类。

    该类用于根据给定的参数判断股票的成交量是否符合特定的模式，以辅助投资决策。
    """

    def __init__(self, signal=1, mode='any', volume_window=60, stddev_mult=1.0):
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

    def match(self, stock, prices, df):
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

        # 检测成交量转折点
        turning_point_indexes, turning_up, turning_down = detect_turning_points(df['volume'])
        turning_idx = turning_up if self.signal == 1 else turning_down
        is_volume_turning = any(idx >= len(df) - 4 for idx in turning_idx)

        # 根据模式返回匹配结果
        if self.mode == 'heavy':
            return is_heavy_volume
        elif self.mode == 'light':
            return is_light_volume
        elif self.mode == 'turning_up':
            return is_volume_turning if self.signal == 1 else False
        elif self.mode == 'turning_down':
            return is_volume_turning if self.signal == -1 else False
        elif self.mode == 'any':
            if self.signal == 1:
                return is_heavy_volume or is_light_volume or is_volume_turning
            else:
                return is_heavy_volume or is_light_volume or is_volume_turning
        else:
            raise ValueError(f"不支持的 mode: {self.mode}")


class OBV:
    label = ''
    signal = 1
    weight = 1

    def __init__(self, signal):
        self.signal = signal
        self.label = 'OBV'

    def match(self, stock, prices, df):
        """
        判断给定股票的最新交易日的OBV指标是否上升。

        参数:
        - stock: 股票标识符，用于识别股票。
        - prices: 包含股票历史价格的列表，每个元素是一个字典。
        - df: 包含股票历史数据的DataFrame，包括close和volume列。

        返回:
        - 如果最新OBV值高于前一个交易日的OBV值，则返回True，否则返回False。
        """
        # 获取最新价格信息
        price = df.iloc[-1]
        # 提取最新成交量并检查是否为正值
        latest_volume = float(price['volume'])
        if not latest_volume > 0:
            # 如果成交量为负，则不进行后续判断，返回False
            return False

        # 计算 OBV 指标
        obv = ta.obv(df['close'], df['volume'])
        turning_point_indexes, turning_up_point_indexes, turning_down_point_indexes = detect_turning_points(obv)
        if not turning_point_indexes:
            return False
        latest_obv = obv.iloc[-1]
        turning_point = obv.iloc[turning_point_indexes[-1]]
        # 判断买入信号
        if self.signal == 1:
            # OBV 上升，确认买入信号
            return latest_obv > turning_point
        else:
            # OBV 下降，确认卖出信号
            return latest_obv < turning_point


class ADOSC:
    label = ''
    signal = 1
    weight = 1

    def __init__(self, signal, threshold=5000):
        self.signal = signal
        self.label = 'ADOSC'
        self.threshold = threshold

    def match(self, stock, prices, df):
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
        turning_point_indexes, turning_up_point_indexes, turning_down_point_indexes = detect_turning_points(adosc)
        if not turning_point_indexes:
            return False
        # 获取最新的 ADOSC 值和前一个 ADOSC 值
        latest = adosc.iloc[-1]
        turning_point = adosc.iloc[turning_point_indexes[-1]]

        # 判断买入信号
        if self.signal == 1:
            return latest > turning_point and latest > self.threshold
        # 判断卖出信号
        else:
            return latest < turning_point and latest < 0


class ADLine:
    def __init__(self, signal=1):
        self.signal = signal
        self.label = 'ADLine'
        self.weight = 1

    def match(self, stock, prices, df):
        if df is None or len(df) < 3:
            print(f'{stock["code"]} 数据不足，无法计算 ADLine')
            return False
        price = df.iloc[-1]
        latest_volume = float(price['volume'])
        if not latest_volume > 0:
            return False
        ad_line = ta.ad(df['high'], df['low'], df['close'], df['volume'])
        turning_point_indexes, turning_up_point_indexes, turning_down_point_indexes = detect_turning_points(ad_line)
        if not turning_point_indexes:
            return False
        latest = ad_line.iloc[-1]
        turning_point = ad_line.iloc[turning_point_indexes[-1]]
        if self.signal == 1:
            return latest > turning_point
        elif self.signal == -1:
            return latest < turning_point
        else:
            raise ValueError("无效的 signal 值，应为 1（买入）或 -1（卖出）")


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
        turning_point_indexes, turning_up_point_indexes, turning_down_point_indexes = detect_turning_points(cmf)
        if not turning_point_indexes:
            return False
        latest = cmf.iloc[-1]
        turning_point = cmf.iloc[turning_point_indexes[-1]]

        dead_zone = 0.05  # 中性带

        # 买入信号：CMF 上升且为正
        if self.signal == 1:
            # 连续上升 + 当前为正 + 高于中性带
            return latest > turning_point and latest > dead_zone

        # 卖出信号：CMF 下降且为负
        elif self.signal == -1:
            # 连续下降 + 当前为负 + 低于中性带
            return latest < turning_point and latest < -dead_zone

        else:
            raise False


class MFI:
    def __init__(self, signal=1, period=14):
        """
        初始化 Money Flow Index（MFI）策略

        参数:
        - signal: 1 表示买入信号（MFI 上升并脱离超卖区），-1 表示卖出信号（MFI 下降并脱离超买区）
        - period: MFI 计算周期，默认为 14
        """
        self.signal = signal
        self.period = period
        self.label = f'MFI{period}'
        self.weight = 1

    def match(self, stock, prices, df, overbought=80, oversold=20):
        if df is None or len(df) < self.period + 3:
            print(f'{stock["code"]} 数据不足，无法计算 MFI 指标')
            return False

        # 获取最新价格信息
        price = df.iloc[-1]
        latest_volume = float(price['volume'])
        if not latest_volume > 0:
            return False

        # 计算 MFI 指标
        mfi = ta.mfi(df['high'], df['low'], df['close'], df['volume'], length=self.period)
        turning_point_indexes, turning_up_point_indexes, turning_down_point_indexes = detect_turning_points(mfi)
        if not turning_point_indexes:
            return False
        latest = mfi.iloc[-1]
        prev = mfi.iloc[-2]
        turning_point = mfi.iloc[turning_point_indexes[-1]]

        # 买入信号：MFI 连续上升 + 上穿超卖区
        if self.signal == 1:
            return turning_point < latest and prev < oversold < latest

        # 卖出信号：MFI 连续下降 + 下穿超买区
        elif self.signal == -1:
            return turning_point > latest and prev > overbought > latest

        else:
            raise ValueError("无效的 signal 值，应为 1（买入）或 -1（卖出）")


def calculate_vpt(close, volume):
    vpt = [0]
    for i in range(1, len(close)):
        change_pct = (close.iloc[i] - close.iloc[i - 1]) / close.iloc[i - 1] if close.iloc[i - 1] != 0 else 0
        vpt.append(vpt[-1] + change_pct * volume.iloc[i])
    return pd.Series(vpt, index=close.index)


class VPT:
    def __init__(self, signal=1, period=3, normalize=True):
        self.signal = signal
        self.period = period
        self.label = f'VPT{period}'
        self.weight = 1
        self.normalize = normalize

    def match(self, stock, prices, df):
        if df is None or len(df) < self.period + 2:
            print(f'{stock["code"]} 数据不足，无法计算 VPT')
            return False
        if df['volume'].iloc[-1] <= 0:
            return False
        vpt = calculate_vpt(df['close'], df['volume'])
        recent_vpt = vpt.iloc[-(self.period + 1):]
        if self.normalize:
            recent_vpt = (recent_vpt - recent_vpt.mean()) / recent_vpt.std() if recent_vpt.std() != 0 else recent_vpt
        diffs = recent_vpt.diff().dropna()
        if self.signal == 1:
            return all(d > 0 for d in diffs)
        elif self.signal == -1:
            return all(d < 0 for d in diffs)
        else:
            raise ValueError("无效的 signal 值，应为 1（买入）或 -1（卖出）")


def get_breakthrough_up_volume_pattern():
    return [VOL(1), OBV(1), ADLine(1), CMF(1), MFI(1), VPT(1)]


def get_breakthrough_down_volume_pattern():
    return [VOL(1), OBV(-1), ADLine(-1), CMF(-1), MFI(-1), VPT(-1)]


def get_oversold_volume_patterns():
    return [VOL(-1), OBV(1), ADLine(1), ADOSC(1), CMF(1), MFI(1), VPT(1)]


def get_overbought_volume_patterns():
    return [VOL(1), OBV(-1), ADLine(-1), ADOSC(-1), CMF(-1), MFI(-1), VPT(-1)]


def detect_turning_points(series: pd.Series,
                          order: int = 5,
                          min_distance: int = 3,
                          min_amplitude: float = 0.01,
                          use_relative: bool = True):
    """
    检测转折点（极大值/极小值），并使用最小距离与最小振幅过滤。

    参数:
    - series: 待分析的Series（如收盘价、成交量等）
    - order: 局部极值判断的窗口宽度
    - min_distance: 相邻转折点的最小索引间距
    - min_amplitude: 最小振幅变化（绝对值或百分比）
    - use_relative: 振幅是否使用相对比例（百分比）

    返回:
    - turning_indexes: 所有保留的转折点索引
    - turning_ups: 极小值点索引
    - turning_downs: 极大值点索引
    """

    # 找局部极大值和极小值
    maxima_idx = argrelextrema(series.values, np.greater, order=order)[0]
    minima_idx = argrelextrema(series.values, np.less, order=order)[0]

    # 合并并排序所有转折点
    all_turning = sorted(np.concatenate((maxima_idx, minima_idx)))

    filtered = []
    last_value = None
    last_index = None

    for idx in all_turning:
        current_value = series.iloc[idx]

        if last_index is None:
            filtered.append(idx)
            last_index = idx
            last_value = current_value
            continue

        # 1. 距离过滤
        if idx - last_index < min_distance:
            continue

        # 2. 振幅过滤
        amplitude = abs(current_value - last_value)
        if use_relative:
            base = max(abs(last_value), 1e-6)
            amplitude /= base

        if amplitude >= min_amplitude:
            filtered.append(idx)
            last_index = idx
            last_value = current_value

    # 分离高低点
    turning_ups = [idx for idx in filtered if idx in minima_idx]
    turning_downs = [idx for idx in filtered if idx in maxima_idx]

    return filtered, turning_ups, turning_downs
