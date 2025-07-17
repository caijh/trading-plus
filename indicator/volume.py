import pandas as pd
import pandas_ta as ta

from calculate.service import detect_turning_points


class VOL:
    def __init__(self, ma=20, signal=1, threshold=1.2):
        """
        初始化 VOL 策略

        参数:
        - ma: 长期均线周期（默认20）
        - signal: 1 表示买入信号，-1 表示卖出信号
        - threshold: 放量或缩量的强度倍数，如 1.2 表示需放大/缩小20%
        """
        self.ma = ma
        self.signal = signal
        self.label = f'VOL{self.ma}'
        self.weight = 1
        self.threshold = threshold

    def match(self, stock, prices, df):
        if df is None or len(df) < max(self.ma, 6):
            print(f'{stock["code"]} 数据不足，无法计算 VOL 指标')
            return False

        # 计算短期和长期的成交量均线
        long_ma = ta.sma(df['volume'], self.ma)
        short_ma = ta.sma(df['volume'], 5)

        if long_ma.isna().iloc[-1] or short_ma.isna().iloc[-1]:
            return False

        # 获取最近成交量均值
        short_vol = short_ma.iloc[-1]
        long_vol = long_ma.iloc[-1]

        # 信号判断
        if self.signal == 1:
            signal = short_vol > (long_vol * self.threshold)
        else:
            signal = short_vol < (long_vol / self.threshold)

        return signal


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
        latest_obv = obv.iloc[-1]
        turning_point_indexes, turning_up_point_indexes, turning_down_point_indexes = detect_turning_points(obv)
        turning_point = obv.iloc[turning_point_indexes[-1]]
        # 判断买入信号
        if self.signal == 1:
            # OBV 上升，确认买入信号
            return turning_point < latest_obv
        else:
            # OBV 下降，确认卖出信号
            return turning_point > latest_obv


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
        # 获取最新的 ADOSC 值和前一个 ADOSC 值
        latest = adosc.iloc[-1]
        turning_point_indexes, turning_up_point_indexes, turning_down_point_indexes = detect_turning_points(adosc)
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
        latest = ad_line.iloc[-1]
        turning_point_indexes, turning_up_point_indexes, turning_down_point_indexes = detect_turning_points(ad_line)
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
        latest = cmf.iloc[-1]
        turning_point_indexes, turning_up_point_indexes, turning_down_point_indexes = detect_turning_points(cmf)
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
        latest = mfi.iloc[-1]
        prev = mfi.iloc[-2]
        turning_point_indexes, turning_up_point_indexes, turning_down_point_indexes = detect_turning_points(mfi)
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
    return [VOL(20, 1), OBV(1), ADLine(1), CMF(1), MFI(1), VPT(1)]


def get_breakthrough_down_volume_pattern():
    return [VOL(20, 1), OBV(-1), ADLine(-1), CMF(-1), MFI(-1), VPT(-1)]


def get_oversold_volume_patterns():
    return [VOL(20, -1), OBV(1), ADLine(1), ADOSC(1), CMF(1), MFI(1), VPT(1)]


def get_overbought_volume_patterns():
    return [VOL(20, 1), OBV(-1), ADLine(-1), ADOSC(-1), CMF(-1), MFI(-1), VPT(-1)]
