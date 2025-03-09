import pandas as pd


class MaPattern:
    ma = 5

    def __init__(self, ma):
        self.ma = ma

    def name(self):
        return f'MA{self.ma}'

    def match(self, stock, prices):
        df = self.create_df(prices)
        price = df.iloc[-1]  # 取最后一行
        pre_price = df.iloc[-2]
        return price['close'] > price['ma'] > pre_price['ma']

    def create_df(self, prices):
        df = pd.DataFrame(prices)
        df['close'] = df['close'].astype(float)
        df['ma'] = df['close'].rolling(self.ma).mean()
        return df


class BiasPattern:
    ma = 5
    bias = 0.15

    def __init__(self, ma, bias):
        self.ma = ma
        self.bias = bias

    def name(self):
        return f'Bias{self.ma}'

    def match(self, stock, prices):
        df = pd.DataFrame(prices)
        df['close'] = df['close'].astype(float)
        df['ma'] = df['close'].rolling(self.ma).mean()
        price = df.iloc[-1]  # 取最后一行
        return price['close'] < price['ma'] and ((price['ma'] - price['close']) / price['ma'] > self.bias)


def get_ma_patterns():
    ma_patterns = [MaPattern(10), MaPattern(20), MaPattern(60), MaPattern(120), MaPattern(200), BiasPattern(25, 0.15)]
    return ma_patterns
