import pandas as pd
import pandas_ta as ta

from calculate.service import detect_turning_points


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
            return is_heavy_volume or is_light_volume or is_volume_turning
        return False


class OBV:
    # 类变量定义
    label = ''
    signal = 1
    weight = 1

    def __init__(self, signal, window=3):
        """
        初始化OBV对象。

        参数:
        - signal: 指示信号类型，1代表买入信号，其他值代表卖出信号。
        - window: 计算OBV指标时考虑的周期，默认为3。
        """
        self.signal = signal
        self.label = 'OBV'
        self.window = window

    def match(self, stock, prices, df):
        """
        根据给定的数据判断是否满足OBV买入或卖出信号。

        参数:
        - stock: 股票信息，未在本函数中使用。
        - prices: 价格信息，未在本函数中使用。
        - df: 包含股票数据的DataFrame，包括['close'（收盘价）和 'volume'（成交量）]列。

        返回:
        - 如果满足买入或卖出信号则返回True，否则返回False。
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
        # 检测 OBV 曲线的拐点
        turning_point_indexes, turning_up_point_indexes, turning_down_point_indexes = detect_turning_points(obv)
        if not turning_point_indexes:
            # 如果没有检测到拐点，返回False
            return False
        # 获取最新OBV值和最近的拐点值
        latest_obv = obv.iloc[-1]
        prev_obv = obv.iloc[-2]
        # 判断买入信号
        if self.signal == 1:
            # OBV 上升，确认买入信号
            turning_up_points = obv.iloc[turning_up_point_indexes]
            turning_up_point_1 = turning_up_points.iloc[-1]
            turning_up_point_2 = turning_up_points.iloc[-2]
            return latest_obv > prev_obv and turning_up_point_1 >= turning_up_point_2
        elif self.signal == -1:
            turning_down_points = obv.iloc[turning_down_point_indexes]
            turning_down_point_1 = turning_down_points.iloc[-1]
            turning_down_point_2 = turning_down_points.iloc[-2]
            # OBV 下降，确认卖出信号
            return latest_obv < prev_obv and turning_down_point_1 <= turning_down_point_2
        return False


class ADOSC:
    label = ''
    signal = 1
    weight = 1

    def __init__(self, signal, threshold=5000, window=3):
        self.signal = signal
        self.label = 'ADOSC'
        self.threshold = threshold
        self.window = window

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
        # 获取最新的 ADOSC 值和前一个 ADOSC 值
        latest = adosc.iloc[-1]
        diff = adosc.diff().iloc[-self.window:]

        if self.signal == 1:
            return (diff > 0).all() and latest > self.threshold
        elif self.signal == -1:
            return (diff < 0).all() and latest < -self.threshold
        return False


class ADLine:
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
        self.label = 'ADLine'
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
        diff = ad_line.diff().iloc[-self.window:]

        if self.signal == 1:
            return (diff > 0).all()
        elif self.signal == -1:
            return (diff < 0).all()
        return False


class CMF:
    def __init__(self, signal=1, period=10):
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
        prev = cmf.iloc[-2]
        dead_zone = 0.05  # 中性带

        # 买入信号：CMF 上升且为正
        if self.signal == 1:
            # 连续上升 + 当前为正 + 高于中性带
            return (latest > prev and latest > dead_zone) or latest < -0.2

        # 卖出信号：CMF 下降且为负
        elif self.signal == -1:
            # 连续下降 + 当前为负 + 低于中性带
            return (latest < prev and latest < -dead_zone) or latest > 0.2

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
        latest = mfi.iloc[-1]
        prev = mfi.iloc[-2]

        if self.signal == 1:
            return prev < latest < oversold

        elif self.signal == -1:
            return prev > latest > overbought

        return False


class VPT:
    """
    VPT 指标计算类。

    Attributes:
        signal (int): 信号类型，1 表示买入信号，-1 表示卖出信号。
        window (int): 计算周期。
        label (str): 标识字符串，用于标识 VPT 和周期。
        weight (int): 权重，默认为 1。
    """

    def __init__(self, signal=1, window=5):
        """
        初始化 VPT 实例。

        Args:
            signal (int, optional): 信号类型，默认为 1（买入信号）。
            window (int, optional): 计算周期，默认为 3。
        """
        self.signal = signal
        self.label = f'VPT{window}'
        self.weight = 1
        self.window = window

    def match(self, stock, prices, df):
        """
        判断当前数据是否满足 VPT 信号条件。

        Args:
            stock (dict): 股票信息字典。
            prices (list): 价格列表，未使用。
            df (pd.DataFrame): 包含股票数据的 DataFrame，包括 'close' 和 'volume' 列。

        Returns:
            bool: 如果满足信号条件返回 True，否则返回 False。
        """
        # 检查数据长度是否足够计算 VPT
        if df is None or len(df) < self.window + 2:
            print(f'{stock["code"]} 数据不足，无法计算 VPT')
            return False
        # 检查最新成交量是否有效
        if df['volume'].iloc[-1] <= 0:
            return False
        # 计算 VPT 值
        vpt = (df['close'].pct_change().fillna(0) * df['volume']).cumsum()
        # 获取最近的 VPT 值
        recent = vpt.iloc[-self.window:]
        # 计算 VPT 斜率
        slope = (recent.iloc[-1] - recent.iloc[0]) / self.window
        # 根据信号类型判断是否满足条件
        if self.signal == 1:
            return slope > 0
        elif self.signal == -1:
            return slope < 0
        return False


def get_breakthrough_up_volume_pattern():
    return [VOL(1), OBV(1), ADLine(1), CMF(1), MFI(1), VPT(1)]


def get_breakthrough_down_volume_pattern():
    return [VOL(1), OBV(-1), ADLine(-1), CMF(-1), MFI(-1), VPT(-1)]


def get_oversold_volume_patterns():
    return [VOL(-1), OBV(1), ADLine(1), ADOSC(1), CMF(1), MFI(1), VPT(1)]


def get_overbought_volume_patterns():
    return [VOL(1), OBV(-1), ADLine(-1), ADOSC(-1), CMF(-1), MFI(-1), VPT(-1)]
