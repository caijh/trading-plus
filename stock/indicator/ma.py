import pandas_ta as ta

from stock.indicator.volume import VOL, OBV, ADOSC


class SMA:
    ma = 5
    label = ''
    signal = 1
    weight = 1

    def __init__(self, ma, signal):
        self.ma = ma
        self.signal = signal
        self.label = f'MA{self.ma}'

    def match(self, stock, prices, df):
        """
        判断股票价格MA是否发生金叉或死叉。

        参数:
        stock: 字典，包含股票信息。
        prices: 列表，包含股票价格历史数据。
        df: DataFrame，包含股票的DataFrame数据，至少包含['close']列。

        返回:
        布尔值，如果发生金叉或死叉，则返回True，否则返回False。
        """
        if len(prices) < self.ma:
            return False

        # 获取最新价格数据
        price = df.iloc[-1]

        # 计算指定周期的简单移动平均线
        df[f'{self.label}'] = ta.sma(df['close'], self.ma)
        ma = df[f'{self.label}']
        # 获取最新和前一均线价格，用于比较
        ma_price = round(ma.iloc[-1], 3)
        pre_ma_price = round(ma.iloc[-2], 3) if len(ma) > 1 else None

        # 使用Technical Analysis库计算收盘价的5日指数移动平均(EMA)
        ema = ta.ema(df['close'], 5)
        # 获取最新的EMA值
        latest_ema = ema.iloc[-1]
        # 获取次新的EMA值
        pre_latest_ema = ema.iloc[-2] if len(ema) > 1 else None

        close_price = price['close']

        if pre_ma_price is None or pre_latest_ema is None:
            return False

        if self.signal == 1:
            # EMA大于SMA，且向上拐，股价在EMA上方
            return (close_price > latest_ema) and (latest_ema > ma_price) and (pre_latest_ema <= pre_ma_price)
        else:
            # EMA小于SMA，且向下拐，股价在EMA下方
            return (close_price < latest_ema) and (latest_ema < ma_price) and (pre_latest_ema >= pre_ma_price)

    def get_volume_confirm_patterns(self):
        if self.signal == 1:
            return [VOL(20, 1), OBV(1), ADOSC(1)]
        return [VOL(20, 1), OBV(-1), ADOSC(-1)]


class VWAP:
    label = 'VWAP'
    weight = 1

    def __init__(self, signal=1, volume_lookback=20):
        """
        初始化 VWAP 策略类
        :param signal: 1 = 买入，-1 = 卖出
        :param volume_lookback: 量能平均判断用的历史天数
        """
        self.signal = signal
        self.volume_lookback = volume_lookback

    def match(self, stock, prices, df):
        """
        使用 VWAP 判断买卖点。
        :param stock: 股票信息字典
        :param prices: 价格信息（未使用）
        :param df: 包含 open/high/low/close/volume 的 DataFrame
        :return: 是否发出信号
        """
        if len(df) < max(3, self.volume_lookback + 1):
            print(f"{stock['code']} 数据不足")
            return False

        df['VWAP'] = df.ta.vwap(high='high', low='low', close='close', volume='volume')

        # 最近两天价格与VWAP
        close_price = df.iloc[-1]['close']
        close_pre_price = df.iloc[-2]['close']
        vwap_today = df.iloc[-1]['VWAP']
        vwap_yesterday = df.iloc[-2]['VWAP']

        # 量能确认：当前成交量 > 过去N天均值
        avg_volume = df['volume'].iloc[-self.volume_lookback - 1:-1].mean()
        volume = df['volume'].iloc[-1]
        volume_confirm = volume > avg_volume

        if self.signal == 1:
            # 买入信号：股价上穿 VWAP 且量能支持
            price_cross = (close_pre_price < vwap_yesterday) and (close_price > vwap_today)
            result = price_cross and volume_confirm
        else:
            # 卖出信号：股价下穿 VWAP 且无需量能支持
            price_cross = (close_pre_price > vwap_yesterday) and (close_price < vwap_today)
            result = price_cross

        return result

    def get_volume_confirm_patterns(self):
        if self.signal == 1:
            return [VOL(20, 1), OBV(1), ADOSC(1)]
        return [VOL(20, 1), OBV(-1), ADOSC(-1)]


class MACD:
    label = ''
    signal = 1
    weight = 1
    recent = 3

    def __init__(self, signal, recent=3):
        self.label = 'MACD'
        self.signal = signal
        self.recent = recent

    def match(self, stock, prices, df):
        """
        根据MACD指标匹配买卖信号。

        参数:
        - stock: 股票信息字典，包含股票代码等信息。
        - prices: 价格数据，未在函数中使用，可考虑移除。
        - df: 包含股票收盘价等数据的DataFrame。

        返回:
        - 如果signal为1，则返回MACD金叉信号。
        - 否则返回MACD死叉信号。
        """
        # 计算MACD指标
        macd_df = ta.macd(df['close'])

        # 重命名列
        macd_df.rename(columns={'MACD_12_26_9': 'MACD', 'MACDs_12_26_9': 'Signal', 'MACDh_12_26_9': 'Histogram'},
                       inplace=True)

        # 检查数据长度是否足够
        if len(macd_df) < 5:
            print(f'{stock["code"]} 数据不足，无法判断金叉或死叉。')
            return False

        # 根据self.signal识别是买卖信号
        if self.signal == 1:
            # 识别并标记MACD金叉信号
            macd_df['Buy_Signal'] = (macd_df['MACD'].shift(1) < macd_df['Signal'].shift(1)) & (
                macd_df['MACD'] > macd_df['Signal'])
            # 判断柱状图是否为正且增大
            macd_df['Histogram_Positive'] = macd_df['Histogram'] > 0
            macd_df['Histogram_Increasing'] = macd_df['Histogram'] > macd_df['Histogram'].shift(1)
            # 结合金叉和柱状图的正值增大情况
            df[f'{self.label}_Signal'] = macd_df['Buy_Signal'] & macd_df['Histogram_Positive'] & macd_df[
                'Histogram_Increasing']

            # 检查最近3个信号中是否有金叉
            recent_signals = df.tail(self.recent)
            macd_buy_signal = recent_signals[f'{self.label}_Signal'].any()
            return macd_buy_signal
        else:
            # 识别并标记MACD死叉信号
            macd_df['Sell_Signal'] = (macd_df['MACD'].shift(1) > macd_df['Signal'].shift(1)) & (
                macd_df['MACD'] < macd_df['Signal'])
            # 判断柱状图是否为负且增大
            macd_df['Histogram_Negative'] = macd_df['Histogram'] < 0
            macd_df['Histogram_Decreasing'] = macd_df['Histogram'] < macd_df['Histogram'].shift(1)
            # 结合死叉和柱状图的负值增大情况
            df[f'{self.label}_Signal'] = macd_df['Sell_Signal'] & macd_df['Histogram_Negative'] & macd_df[
                'Histogram_Decreasing']

            # 检查最近3个信号中是否有死叉
            recent_signals = df.tail(self.recent)
            macd_sell_signal = recent_signals[f'{self.label}_Signal'].any()
            return macd_sell_signal

    def get_volume_confirm_patterns(self):
        if self.signal == 1:
            return [VOL(20, 1), OBV(1), ADOSC(1)]
        return [VOL(20, 1), OBV(-1), ADOSC(-1)]


class BIAS:
    ma = 5
    bias = -0.15
    label = ''
    signal = 1
    weight = 1

    def __init__(self, ma, bias, signal):
        self.signal = signal
        self.ma = ma
        self.bias = bias
        self.label = f'Bias{self.ma}'

    def match(self, stock, prices, df):
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
        if self.signal == 1:
            return [VOL(20, -1), OBV(1), ADOSC(1)]
        return [VOL(20, 1), OBV(-1), ADOSC(-1)]


class KDJ:
    label = ''
    signal = 1
    weight = 1

    def __init__(self, signal, recent=3):
        self.signal = signal
        self.label = 'KDJ'
        self.recent = recent

    def match(self, stock, prices, df):
        # 计算 KDJ 指标
        kdj_df = df.ta.stoch(high='high', low='low', close='close', k=9, d=3, smooth_d=3)

        # 重命名列
        kdj_df.rename(columns={'STOCHk_9_3_3': 'K', 'STOCHd_9_3_3': 'D'}, inplace=True)

        if self.signal == 1:
            # 识别 KDJ 金叉（K 上穿 D，且 D < 20）
            df[f'{self.label}_Signal'] = (kdj_df['K'].shift(1) < kdj_df['D'].shift(1)) & (kdj_df['K'] > kdj_df['D']) & (
                kdj_df['D'] < 20)
        elif self.signal == -1:
            # 识别 KDJ 死叉（K 下穿 D，且 D > 80）
            df[f'{self.label}_Signal'] = (kdj_df['K'].shift(1) > kdj_df['D'].shift(1)) & (kdj_df['K'] < kdj_df['D']) & (
                kdj_df['D'] > 80)
        else:
            raise ValueError("signal 参数只能是 1（金叉）或 -1（死叉）")

        # 取最近几天数据
        recent_signals = df.tail(self.recent)

        # 判断是否有交易信号
        kdj_signal = recent_signals[f'{self.label}_Signal'].any()

        return kdj_signal

    def get_volume_confirm_patterns(self):
        if self.signal == 1:
            return [VOL(20, -1), OBV(1), ADOSC(1)]
        return [VOL(20, 1), OBV(-1), ADOSC(-1)]


class RSI:
    weight = 1
    signal = 1
    recent = 3

    def __init__(self, signal, recent=3):
        self.signal = signal
        self.label = 'RSI'
        self.recent = recent

    def match(self, stock, prices, df):
        # 计算 RSI 指标
        rsi_df = ta.rsi(df['close'], length=14, signal_indicators=True)
        # 重命名列
        rsi_df.rename(columns={'RSI_14': 'RSI'}, inplace=True)
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
        if self.signal == 1:
            return [VOL(20, -1), OBV(1), ADOSC(1)]
        return [VOL(20, 1), OBV(-1), ADOSC(-1)]


class WR:
    weight = 1
    signal = 1
    recent = 3

    def __init__(self, signal=1, recent=3):
        """
        :param signal: 1 表示买入，-1 表示卖出
        :param recent: 最近 N 天内是否出现信号
        """
        self.signal = signal
        self.label = 'WR'
        self.recent = recent

    def match(self, stock, prices, df):
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
        if self.signal == 1:
            return [VOL(20, -1), OBV(1), ADOSC(1)]
        return [VOL(20, 1), OBV(-1), ADOSC(-1)]


class CCI:
    signal = 1  # 1 表示买入信号，-1 表示卖出信号
    weight = 1
    period = 20

    def __init__(self, signal, period=20, recent=3):
        self.signal = signal
        self.label = "CCI"
        self.period = period
        self.recent = recent

    def match(self, stock, prices, df):
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
            df[f'{self.label}_Signal'] = (cci_df.shift(1) < -100) & (cci_df > cci_df.shift(1))
        else:
            # 卖出信号：CCI 从高于 100 回落
            df[f'{self.label}_Signal'] = (cci_df.shift(1) > 100) & (cci_df < cci_df.shift(1))

        # 获取最近几天的数据
        recent_signals = df.tail(self.recent)

        # 判断是否出现信号
        signal = recent_signals[f'{self.label}_Signal'].any()

        return signal

    def get_volume_confirm_patterns(self):
        if self.signal == 1:
            return [VOL(20, -1), OBV(1), ADOSC(1)]
        return [VOL(20, 1), OBV(-1), ADOSC(-1)]


def get_up_ma_patterns():
    """
    创建并返回一个包含常用均线和偏差率模式的列表。

    这个函数初始化了一个列表，包含了不同周期的均线（如5日、10日、20日、60日、200日均线），
    以及一个特定参数的偏差率模式。这些模式用于在金融数据分析中计算和应用各种移动平均线和偏差率指标。
    """
    # 初始化均线和偏差率模式列表
    ma_patterns = [SMA(10, 1), SMA(20, 1), SMA(60, 1), SMA(200, 1), MACD(1), VWAP(1),
                   BIAS(20, -0.10, 1), KDJ(1), RSI(1), WR(1), CCI(1)]
    return ma_patterns


def get_down_ma_patterns():
    """
    创建并返回一个包含常用均线和偏差率模式的列表。

    这个函数初始化了一个列表，包含了不同周期的均线（如5日、10日、20日、60日、200日均线），
    以及一个特定参数的偏差率模式。这些模式用于在金融数据分析中计算和应用各种移动平均线和偏差率指标。
    """
    # 初始化均线和偏差率
    ma_patterns = [SMA(10, -1), SMA(20, -1), SMA(60, -1), SMA(200, -1), MACD(-1), VWAP(-1),
                   BIAS(20, 0.10, -1), KDJ(-1), RSI(-1), WR(-1), CCI(-1)]
    return ma_patterns
