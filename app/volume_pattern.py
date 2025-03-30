import pandas_ta as ta


class VolumePattern:
    ma = 20

    def __init__(self, ma):
        self.ma = ma

    def name(self):
        return f'VOL{self.ma}'

    def match(self, stock, prices, df):
        """
        根据给定的股票数据和价格信息，判断当前股票是否满足特定的买卖条件。

        参数:
        - stock: 股票标识符，用于唯一标识一只股票。
        - prices: 价格信息，本例中未直接使用，但可能在将来用于更复杂的判断条件。
        - df: 包含股票历史数据的DataFrame，包括但不限于日期、开盘价、收盘价、最高价、最低价和成交量。

        返回:
        - True 如果当前股票价格相较于前一日上涨且成交量有效放大（超过均线值）；
        - False 如果当前股票价格相较于前一日下跌且成交量有效缩小（低于均线值）。
        """
        # 将成交量转换为浮点数类型，以支持后续的计算
        df['volume'] = df['volume'].astype(float)

        # 计算成交量的移动平均值，使用简单移动平均线（SMA）
        ma = ta.sma(df['volume'], self.ma)

        # 取当前（最新）的交易数据
        price = df.iloc[-1]
        # 取前一个交易日的数据，用于比较
        pre_price = df.iloc[-2]

        # 从移动平均线中提取当前和前一个交易日的成交量均线值
        ma_volume = ma.iloc[-1]

        # 判断当前收盘价是否高于前一个交易日的收盘价
        if price['close'] > pre_price['close']:
            # 上涨，返回当前成交量大于上一日成交量且大于均线值
            return price['volume'] > pre_price['volume'] > ma_volume
        else:
            # 下跌，返回当前成交量是否小于上一日成交量且小于均线值
            return price['volume'] < pre_price['volume'] < ma_volume


class OBV:
    def name(self):
        return 'OBV'

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
        price = prices[-1]
        # 提取最新成交量并检查是否为正值
        latest_volume = float(price['volume'])
        if not latest_volume > 0:
            # 如果成交量为负，则不进行后续判断，返回False
            return False

        # 计算OBV指标
        obv = ta.obv(df['close'], df['volume'])
        # 提取最新和前一个OBV值
        latest_obv = obv.iloc[-1]
        pre_obv = obv.iloc[-2]

        # 判断最新OBV值是否较前一个交易日有所上升
        return latest_obv > pre_obv


class ADOSC:
    def name(self):
        return 'ADOSC'

    def match(self, stock, prices, df):
        price = prices[-1]
        latest_volume = float(price['volume'])
        if not latest_volume > 0:
            return False

        adosc = ta.adosc(df['high'], df['low'], df['close'], df['volume'])
        latest_adosc = adosc.iloc[-1]
        pre_adosc = adosc.iloc[-2]

        pre_price = prices[-2]
        close_price = float(price['close'])
        pre_close_price = float(pre_price['close'])
        return latest_adosc > pre_adosc and close_price > pre_close_price

def get_volume_patterns():
    """
    获取成交量模式列表。

    Returns:
        list: 包含一个成交量模式对象的列表。
    """
    return [VolumePattern(20), OBV(), ADOSC()]
