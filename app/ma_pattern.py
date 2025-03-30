class MaPattern:
    ma = 5

    def __init__(self, ma):
        self.ma = ma

    def name(self):
        return f'MA{self.ma}'

    def match(self, stock, prices, df):
        df['ma'] = df['close'].rolling(self.ma).mean()
        price = df.iloc[-1]  # 取最后一行
        pre_price = df.iloc[-2]
        return price['close'] > price['ma'] > pre_price['ma']



class BiasPattern:
    ma = 5
    bias = 0.15

    def __init__(self, ma, bias):
        self.ma = ma
        self.bias = bias

    def name(self):
        return f'Bias{self.ma}'

    def match(self, stock, prices, df):
        df['ma'] = df['close'].rolling(self.ma).mean()
        price = df.iloc[-1]  # 取最后一行
        return price['close'] < price['ma'] and ((price['ma'] - price['close']) / price['ma'] > self.bias)


def get_ma_patterns():
    """
    创建并返回一个包含常用均线和偏差率模式的列表。

    这个函数初始化了一个列表，包含了不同周期的均线（如5日、10日、20日、60日、200日均线），
    以及一个特定参数的偏差率模式。这些模式用于在金融数据分析中计算和应用各种移动平均线和偏差率指标。
    """
    # 初始化均线和偏差率模式列表
    ma_patterns = [MaPattern(10), MaPattern(20), MaPattern(60), MaPattern(200), BiasPattern(25, 0.15)]
    return ma_patterns
