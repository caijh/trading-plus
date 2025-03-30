class VolumePattern:
    ma = 20

    def __init__(self, ma):
        self.ma = ma

    def name(self):
        return f'VOL{self.ma}'

    def match(self, stock, prices, df):
        df['volume'] = df['volume'].astype(float)
        df['volume_ma'] = df['volume'].rolling(self.ma).mean()
        price = df.iloc[-1]  # 取最后一行
        pre_price = df.iloc[-2]
        return price['volume'] > price['volume_ma'] > pre_price['volume_ma']

def get_volume_patterns():
    return [VolumePattern(20)]
