import pandas_ta as ta


class MA:
    ma = 5
    label = ''
    signal = 1

    def __init__(self, ma, signal):
        self.ma = ma
        self.signal = signal
        self.label = f'MA{self.ma}'

    def match(self, stock, prices, df):
        """
        判断股票价格MA是否如果金叉。

        参数:
        stock: 字典，包含股票信息。
        prices: 列表，包含股票价格历史数据。
        df: DataFrame，包含股票的DataFrame数据，至少包含['close']列。

        返回:
        布尔值，如果金叉，则返回True，否则返回False。
        """

        if len(prices) < self.ma:
            return False

        # 获取最新价格数据
        price = df.iloc[-1]

        # 计算指定周期的简单移动平均线
        ma = ta.sma(df['close'], self.ma)
        print(ma)
        # 获取最新和前一均线价格，用于比较
        ma_price = round(ma.iloc[-1], 3)  # 取最后一行
        pre_ma_price = round(ma.iloc[-2], 3)

        # 使用Technical Analysis库计算收盘价的5日指数移动平均(EMA)
        ema = ta.ema(df['close'], 5)
        # 获取最新的EMA值
        latest_ema = ema.iloc[-1]
        # 获取次新的EMA值
        pre_latest_ema = ema.iloc[-2]

        # 打印计算结果，用于调试和日志记录
        print(
            f'{stock["code"]} MA{self.ma}, price = {price["close"]}, ma_price = {ma_price}, pre_ma_price = {pre_ma_price}, latest_ema = {latest_ema}, pre_latest_ema = {pre_latest_ema}')

        if self.signal == 1:
            # 返回最新EMA值高于MA价格且前一EMA值低于前一MA价格的情况
            return (latest_ema > ma_price) and (pre_latest_ema < pre_ma_price)
        else:
            return (latest_ema < ma_price) and (pre_latest_ema > pre_ma_price)


class BIAS:
    ma = 5
    bias = -0.15
    label = ''
    signal = 1

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
        - df: 包含股票历史数据的DataFrame，必须至少包含'close'列，代表收盘价。

        返回:
        - True：如果股票满足买入条件，即最新收盘价的偏差率小于0且小于预设的偏差阈值。
        - False：否则。
        """
        # 计算股票收盘价的偏差率
        bias = ta.bias(df['close'], self.ma)
        # 获取最新的偏差率值
        latest_bias = bias.iloc[-1]
        print(f'Stock {stock["code"]} 偏差率值为{latest_bias}, 期望值为{self.bias}')
        # 判断最新偏差率是否满足买入条件
        if self.signal == 1:
            return latest_bias < 0 and latest_bias < self.bias
        else:
            return latest_bias > 0 and latest_bias > self.bias


class MACD:
    label = ''
    signal = 1

    def __init__(self, signal):
        self.label = 'MACD'

    def match(self, stock, prices, df):
        macd_df = ta.macd(df['close'])

        # 重命名列
        macd_df.rename(columns={'MACD_12_26_9': 'MACD', 'MACDs_12_26_9': 'Signal', 'MACDh_12_26_9': 'Histogram'},
                       inplace=True)

        # 识别交易信号
        if self.signal == 1:
            macd_df['Buy_Signal'] = (macd_df['MACD'].shift(1) < macd_df['Signal'].shift(1)) & (
                    macd_df['MACD'] > macd_df['Signal'])  # 金叉
            recent_signals = macd_df.tail(5)
            macd_buy_signal = recent_signals['Buy_Signal'].any()
            print(f'{stock["code"]} MACD 是否金叉 = {macd_buy_signal}')
            return macd_buy_signal
        else:
            macd_df['Sell_Signal'] = (macd_df['MACD'].shift(1) > macd_df['Signal'].shift(1)) & (
                    macd_df['MACD'] < macd_df['Signal'])  # 死叉
            recent_signals = macd_df.tail(5)
            macd_sell_signal = recent_signals['Sell_Signal'].any()
            print(f'{stock["code"]} MACD 是否死叉 = {macd_sell_signal}')


class KDJ:
    label = ''
    signal = 1

    def __init__(self, signal):
        self.signal = signal
        self.label = 'KDJ'

    def match(self, stock, prices, df):
        # 计算 KDJ 指标
        kdj_df = df.ta.stoch(high='high', low='low', close='close', k=9, d=3, smooth_d=3)

        # 重命名列
        kdj_df.rename(columns={'STOCHk_9_3_3': 'K', 'STOCHd_9_3_3': 'D'}, inplace=True)

        if self.signal == 1:
            # 识别 KDJ 金叉（K 上穿 D，且 K < 20）
            kdj_df['Signal'] = (kdj_df['K'].shift(1) < kdj_df['D'].shift(1)) & (kdj_df['K'] > kdj_df['D']) & (
                    kdj_df['K'] < 20)
        elif self.signal == -1:
            # 识别 KDJ 死叉（K 下穿 D，且 K > 80）
            kdj_df['Signal'] = (kdj_df['K'].shift(1) > kdj_df['D'].shift(1)) & (kdj_df['K'] < kdj_df['D']) & (
                    kdj_df['K'] > 80)
        else:
            raise ValueError("signal 参数只能是 1（金叉）或 -1（死叉）")

        # 取最近 5 天数据
        recent_signals = kdj_df.tail(5)

        # 判断是否有交易信号
        kdj_signal = recent_signals['Signal'].any()

        action = "金叉 (买入)" if self.signal == 1 else "死叉 (卖出)"
        print(f'{stock["code"]} KDJ 是否 {action} = {kdj_signal}')
        return kdj_signal


class RSI:
    def __init__(self, signal=1):
        self.signal = signal
        self.label = 'RSI'

    def match(self, stock, prices, df):
        # 计算 RSI 指标
        rsi_df = ta.rsi(df['close'], length=14, signal_indicators=True)
        # 重命名列
        rsi_df.rename(columns={'RSI_14': 'RSI'}, inplace=True)
        if self.signal == 1:
            # 识别 RSI 低于 30 且反弹（买入信号）
            rsi_df['Signal'] = (rsi_df['RSI'].shift(1) < 30) & (rsi_df['RSI'] > rsi_df['RSI'].shift(1))
        elif self.signal == -1:
            # 识别 RSI 高于 70 且下跌（卖出信号）
            rsi_df['Signal'] = (rsi_df['RSI'].shift(1) > 70) & (rsi_df['RSI'] < rsi_df['RSI'].shift(1))
        else:
            raise ValueError("signal 参数只能是 1（买入）或 -1（卖出）")

        # 取最近 5 天数据
        recent_signals = rsi_df.tail(5)

        # 判断是否有交易信号
        rsi_signal = recent_signals['Signal'].any()

        action = "买入" if self.signal == 1 else "卖出"
        print(f'{stock["code"]} RSI 是否 {action} = {rsi_signal}')
        return rsi_signal


def get_up_ma_patterns():
    """
    创建并返回一个包含常用均线和偏差率模式的列表。

    这个函数初始化了一个列表，包含了不同周期的均线（如5日、10日、20日、60日、200日均线），
    以及一个特定参数的偏差率模式。这些模式用于在金融数据分析中计算和应用各种移动平均线和偏差率指标。
    """
    # 初始化均线和偏差率模式列表
    ma_patterns = [MA(10, 1), MA(20, 1), MA(60, 1), MA(120, 1), MA(200, 1), BIAS(20, -0.10, 1), MACD(1), KDJ(1), RSI(1)]
    return ma_patterns


def get_down_ma_patterns():
    """
    创建并返回一个包含常用均线和偏差率模式的列表。

    这个函数初始化了一个列表，包含了不同周期的均线（如5日、10日、20日、60日、200日均线），
    以及一个特定参数的偏差率模式。这些模式用于在金融数据分析中计算和应用各种移动平均线和偏差率指标。
    """
    # 初始化均线和偏差率
    ma_patterns = [MA(10, -1), MA(20, -1), MA(60, -1), MA(120, -1), MA(200, -1), BIAS(20, 0.10, -1), MACD(-1), KDJ(-1),
                   RSI(-1)]
    return ma_patterns
