import pandas_ta as ta


class MA:
    ma = 5
    label = ''

    def __init__(self, ma):
        self.ma = ma
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
        # 获取最新价格数据
        price = df.iloc[-1]

        # 计算指定周期的简单移动平均线
        ma = ta.sma(df['close'], self.ma)

        # 获取最新和前一均线价格，用于比较
        ma_price = round(ma.iloc[-1], 3)  # 取最后一行
        pre_ma_price = round(ma.iloc[-2], 3)

        ema = ta.ema(df['close'], 5)
        latest_ema = ema.iloc[-1]
        pre_latest_ema = ema.iloc[-2]

        # 打印计算结果，用于调试和日志记录
        print(
            f'Cal {stock["code"]} MA{self.ma}, price = {price["close"]}, ma_price = {ma_price}, pre_ma_price = {pre_ma_price}, latest_ema = {latest_ema}, pre_latest_ema = {pre_latest_ema}')

        return (latest_ema > ma_price) and (pre_latest_ema < pre_ma_price)


class BIAS:
    ma = 5
    bias = -0.15
    label = ''

    def __init__(self, ma, bias):
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
        return latest_bias < 0 and latest_bias < self.bias


def get_ma_patterns():
    """
    创建并返回一个包含常用均线和偏差率模式的列表。

    这个函数初始化了一个列表，包含了不同周期的均线（如5日、10日、20日、60日、200日均线），
    以及一个特定参数的偏差率模式。这些模式用于在金融数据分析中计算和应用各种移动平均线和偏差率指标。
    """
    # 初始化均线和偏差率模式列表
    ma_patterns = [MA(10), MA(20), MA(60), MA(120), MA(200), BIAS(25, -0.10)]
    return ma_patterns
