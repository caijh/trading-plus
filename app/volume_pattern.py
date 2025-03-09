import pandas as pd


class VolumePattern:
    ma = 20

    def __init__(self, ma):
        self.ma = ma

    def name(self):
        return f'VOL{self.ma}'

    def match(self, stock, prices):
        df = self.create_df(prices)
        price = df.iloc[-1]  # 取最后一行
        pre_price = df.iloc[-2]
        return price['volume'] > price['ma'] > pre_price['ma']

    def create_df(self, prices):
        df = pd.DataFrame(prices)
        df['volume'] = df['volume'].astype(float)
        df['ma'] = df['volume'].rolling(self.ma).mean()
        return df


def get_volume_patterns():
    return [VolumePattern(20)]
