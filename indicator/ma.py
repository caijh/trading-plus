import pandas as pd
import pandas_ta as ta

from indicator.macd import MACD
from indicator.sma import SMA
from indicator.volume import volume_registry


class SAR:
    name = 'SAR'

    def __init__(self, signal=1):
        """
        Parabolic SAR 策略

        参数:
        - signal: 1 表示买入信号（SAR 从上转到下），-1 表示卖出信号（SAR 从下转到上）
        """
        self.signal = signal
        self.label = 'SAR'
        self.weight = 1

    def match(self, stock, df):
        if df is None or len(df) < 3:
            print(f'{stock["code"]} 数据不足，无法计算 PSAR')
            return False

        # 计算 SAR（默认加速因子 step=0.02, max_step=0.2）
        psar = ta.psar(df['high'], df['low'], df['close'])
        if 'PSARl_0.02_0.2' not in psar.columns or 'PSARs_0.02_0.2' not in psar.columns:
            print(f'{stock["code"]} PSAR计算失败')
            return False

        # 最新一条 SAR 值
        psar_last = psar['PSARl_0.02_0.2'].iloc[-1] if not pd.isna(psar['PSARl_0.02_0.2'].iloc[-1]) else \
            psar['PSARs_0.02_0.2'].iloc[-1]
        psar_prev = psar['PSARl_0.02_0.2'].iloc[-2] if not pd.isna(psar['PSARl_0.02_0.2'].iloc[-2]) else \
            psar['PSARs_0.02_0.2'].iloc[-2]
        close_last = df['close'].iloc[-1]
        close_prev = df['close'].iloc[-2]

        # 买入信号：SAR 从上转到下（之前 close < SAR，当前 close > SAR）
        if self.signal == 1:
            return close_prev < psar_prev and close_last > psar_last

        # 卖出信号：SAR 从下转到上（之前 close > SAR，当前 close < SAR）
        elif self.signal == -1:
            return close_prev > psar_prev and close_last < psar_last

        return False

    def get_volume_confirm_patterns(self):
        return volume_registry.get(self.name).get(self.signal)


class BIAS:
    ma = 5
    bias = -0.15
    label = ''
    signal = 1
    weight = 1
    name = 'BIAS'

    def __init__(self, ma, bias, signal):
        self.signal = signal
        self.ma = ma
        self.bias = bias
        self.label = f'Bias{self.ma}'

    def match(self, stock, df):
        """
        判断给定股票是否满足特定的买入条件。

        本函数使用偏差率指标来评估股票的当前价格是否被低估。
        参数:
        - stock: 股票对象，可能包含股票的基本信息（未在本函数中使用）。
        - prices: 股票价格数据（未在本函数中使用，可能为未来扩展保留）。
        - df: 包含股票历史数据的DataFrame，必须至少包含['close']列，代表收盘价。

        返回:
        - True：如果股票满足买入条件，即最新收盘价的偏差率小于0且小于预设的偏差阈值。
        - False：否则。
        """
        # 计算股票收盘价的偏差率
        if df is None or len(df) < self.ma:
            return False

        df[f'{self.label}'] = ta.bias(df['close'], self.ma)
        bias = df[f'{self.label}']
        # 获取最新的偏差率值
        latest_bias = bias.iloc[-1]
        if self.signal == 1:
            # 下跌，达到偏差值
            return latest_bias < self.bias
        else:
            # 上涨，达到偏差值
            return latest_bias > self.bias

    def get_volume_confirm_patterns(self):
        return volume_registry.get(self.name).get(self.signal)


class KDJ:
    label = ''
    signal = 1
    weight = 1
    name = 'KDJ'

    def __init__(self, signal, recent=1):
        self.signal = signal
        self.label = 'KDJ'
        self.recent = recent

    def match(self, stock, df):
        if df is None or len(df) < 15:
            return False

        # 计算 KDJ 指标
        kdj_df = df.ta.stoch(high='high', low='low', close='close', k=9, d=3, smooth_d=3)

        # 重命名列
        kdj_df.rename(columns={'STOCHk_9_3_3': 'K', 'STOCHd_9_3_3': 'D'}, inplace=True)
        kdj_df['J'] = 3 * kdj_df['K'] - 2 * kdj_df['D']

        if self.signal == 1:
            # 识别 KDJ 金叉（K 上穿 D，且 D < 20）
            df[f'{self.label}_Signal'] = (kdj_df['K'].shift(1) < kdj_df['D'].shift(1)) & (kdj_df['K'] > kdj_df['D']) & (
                kdj_df['D'] < 20) & (kdj_df['J'] < 20)
        elif self.signal == -1:
            # 识别 KDJ 死叉（K 下穿 D，且 D > 80）
            df[f'{self.label}_Signal'] = (kdj_df['K'].shift(1) > kdj_df['D'].shift(1)) & (kdj_df['K'] < kdj_df['D']) & (
                kdj_df['D'] > 80) & (kdj_df['J'] > 80)
        else:
            raise ValueError("signal 参数只能是 1（金叉）或 -1（死叉）")

        # 取最近几天数据
        recent_signals = df.tail(self.recent)

        # 判断是否有交易信号
        kdj_signal = recent_signals[f'{self.label}_Signal'].any()

        return kdj_signal

    def get_volume_confirm_patterns(self):
        return volume_registry.get(self.name).get(self.signal)


class RSI:
    weight = 1
    signal = 1
    recent = 1
    name = 'RSI'

    def __init__(self, signal, recent=3):
        self.signal = signal
        self.label = 'RSI'
        self.recent = recent

    def match(self, stock, df):
        # 计算 RSI 指标
        rsi_df = ta.rsi(df['close'], length=14, signal_indicators=True)  # type: ignore
        # 重命名列
        rsi_df.rename(columns={'RSI_14': 'RSI'}, inplace=True)  # type: ignore
        df[f'{self.label}'] = rsi_df['RSI']
        if self.signal == 1:
            # 识别 RSI 低于 30 且反弹（买入信号）
            df[f'{self.label}_Signal'] = (rsi_df['RSI'].shift(1) < 30) & (rsi_df['RSI'] > rsi_df['RSI'].shift(1))
        elif self.signal == -1:
            # 识别 RSI 高于 70 且下跌（卖出信号）
            df[f'{self.label}_Signal'] = (rsi_df['RSI'].shift(1) > 70) & (rsi_df['RSI'] < rsi_df['RSI'].shift(1))
        else:
            raise ValueError("signal 参数只能是 1（买入）或 -1（卖出）")

        recent_signals = df.tail(self.recent)

        # 判断是否有交易信号
        rsi_signal = recent_signals[f'{self.label}_Signal'].any()

        return rsi_signal

    def get_volume_confirm_patterns(self):
        return volume_registry.get(self.name).get(self.signal)


class WR:
    weight = 1
    signal = 1
    recent = 1
    name = 'WR'

    def __init__(self, signal=1, recent=3):
        """
        :param signal: 1 表示买入，-1 表示卖出
        :param recent: 最近 N 天内是否出现信号
        """
        self.signal = signal
        self.label = 'WR'
        self.recent = recent

    def match(self, stock, df):
        """
        判断是否满足 WR 指标的买入或卖出信号。
        :param stock: 股票信息字典
        :param prices: 未使用，预留参数
        :param df: DataFrame，必须包含 high、low、close
        :return: True / False
        """
        # 计算 WR 指标，默认周期 14
        wr_df = ta.willr(high=df['high'], low=df['low'], close=df['close'], length=14)
        df[self.label] = wr_df

        if self.signal == 1:
            # 买入信号：WR 上穿 -80（从超卖区域反弹）
            df[f'{self.label}_Signal'] = (wr_df.shift(1) < -80) & (wr_df > wr_df.shift(1))
        elif self.signal == -1:
            # 卖出信号：WR 下穿 -20（从超买区域回落）
            df[f'{self.label}_Signal'] = (wr_df.shift(1) > -20) & (wr_df < wr_df.shift(1))
        else:
            raise ValueError("signal 参数只能是 1（买入）或 -1（卖出）")

        # 最近 N 天是否出现信号
        recent_signals = df.tail(self.recent)
        signal = recent_signals[f'{self.label}_Signal'].any()

        return signal

    def get_volume_confirm_patterns(self):
        return volume_registry.get(self.name).get(self.signal)


class CCI:
    signal = 1  # 1 表示买入信号，-1 表示卖出信号
    weight = 1
    period = 20
    name = 'CCI'

    def __init__(self, signal, period=20, recent=3):
        self.signal = signal
        self.label = "CCI"
        self.period = period
        self.recent = recent

    def match(self, stock, df):
        """
        判断CCI指标的买卖信号。

        :param stock: 股票信息字典，包含股票代码等信息。
        :param prices: 价格数据（未使用，可扩展）。
        :param df: 股票历史数据 DataFrame，必须至少包含 ['high', 'low', 'close'] 列。

        :return: True/False，是否出现符合条件的买卖信号。
        """
        # 计算 CCI 指标（通常使用 20 天周期）
        df[f'{self.label}'] = df.ta.cci(length=self.period)

        # 确保 CCI 计算不为空
        if df[f'{self.label}'].isnull().all():
            print(f"CCI 计算失败，数据为空: {stock['code']}")
            return False

        cci_df = df[f'{self.label}']
        # 识别交易信号
        if self.signal == 1:
            # 买入信号：CCI 从低于 -100 反弹
            df[f'{self.label}_Signal'] = (cci_df.shift(1) < -100) & (cci_df > -100)
        else:
            # 卖出信号：CCI 从高于 100 回落
            df[f'{self.label}_Signal'] = (cci_df.shift(1) > 100) & (cci_df < 100)

        # 获取最近几天的数据
        recent_signals = df.tail(self.recent)

        # 判断是否出现信号
        signal = recent_signals[f'{self.label}_Signal'].any()

        return signal

    def get_volume_confirm_patterns(self):
        return volume_registry.get(self.name).get(self.signal)


def get_up_ma_patterns():
    """
    创建并返回一个包含常用均线和偏差率模式的列表。

    这个函数初始化了一个列表，包含了不同周期的均线（如5日、10日、20日、60日、200日均线），
    以及一个特定参数的偏差率模式。这些模式用于在金融数据分析中计算和应用各种移动平均线和偏差率指标。
    """
    # 初始化均线和偏差率模式列表
    ma_patterns = [SMA(10, 1), SMA(20, 1), SMA(50, 1),
                   MACD(1), SAR(1),
                   BIAS(20, -0.09, 1), KDJ(1), RSI(1), WR(1)]
    return ma_patterns


def get_down_ma_patterns():
    """
    创建并返回一个包含常用均线和偏差率模式的列表。

    这个函数初始化了一个列表，包含了不同周期的均线（如5日、10日、20日、60日、200日均线），
    以及一个特定参数的偏差率模式。这些模式用于在金融数据分析中计算和应用各种移动平均线和偏差率指标。
    """
    # 初始化均线和偏差率
    ma_patterns = [SMA(10, -1), SMA(20, -1), SMA(50, -1),
                   MACD(-1), SAR(-1),
                   BIAS(20, 0.09, -1), KDJ(-1), RSI(-1), WR(-1)]
    return ma_patterns


