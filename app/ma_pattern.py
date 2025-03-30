import pandas_ta as ta

class MaPattern:
    ma = 5

    def __init__(self, ma):
        self.ma = ma

    def name(self):
        return f'MA{self.ma}'

    def match(self, stock, prices, df):
        price = df.iloc[-1]
        ma = ta.sma(df['close'], self.ma)
        ma_price = round(ma.iloc[-1], 3)  # 取最后一行
        pre_ma_price = round(ma.iloc[-2], 3)
        print(
            f'Cal {stock["code"]} MA{self.ma}, price = {price["close"]}, ma_price = {ma_price}, pre_ma_price = {pre_ma_price}')
        return price['close'] > ma_price > pre_ma_price



class BiasPattern:
    ma = 5
    bias = -0.15

    def __init__(self, ma, bias):
        self.ma = ma
        self.bias = bias

    def name(self):
        return f'Bias{self.ma}'

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
    ma_patterns = [MaPattern(10), MaPattern(20), MaPattern(60), MaPattern(200), BiasPattern(25, -0.15)]
    return ma_patterns
