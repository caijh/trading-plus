import pandas_ta as ta


class VOL:
    def __init__(self, ma=20, signal=1):
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
            signal = short_vol > (long_vol * 1.1)
        else:
            signal = short_vol < (long_vol * 0.9)

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
        # 提取最新和前一个 OBV 值
        latest_obv = obv.iloc[-1]
        pre_obv = obv.iloc[-2]

        # 判断买入信号
        if self.signal == 1:
            # OBV 上升，确认买入信号
            return latest_obv > pre_obv
        else:
            # OBV 下降，确认卖出信号
            return latest_obv < pre_obv


class ADOSC:
    label = ''
    signal = 1
    weight = 1

    def __init__(self, signal):
        self.signal = signal
        self.label = 'A/D Line'

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
        latest_adosc = adosc.iloc[-1]
        pre_adosc = adosc.iloc[-2]

        # 判断买入信号
        if self.signal == 1:
            return latest_adosc > pre_adosc
        # 判断卖出信号
        else:
            return latest_adosc < pre_adosc
