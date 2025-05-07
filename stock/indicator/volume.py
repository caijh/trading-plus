import pandas_ta as ta


class VOL:
    ma = 20
    label = ''
    signal = 1
    weight = 1

    def __init__(self, ma, signal):
        self.ma = ma
        self.signal = signal
        self.label = f'VOL{self.ma}'

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

        # 计算成交量的变化幅度
        volume_ratio = price['volume'] / ma_volume

        # 判断信号时考虑成交量的波动性
        if self.signal == 1:  # 买入信号
            if price['close'] >= pre_price['close']:  # 股价上涨
                # 判断成交量是否同步放大，且大于均线一定比例
                return price['volume'] > pre_price['volume'] and volume_ratio > 1.1
            else:  # 股价下跌，成交量不应放大
                return price['volume'] <= pre_price['volume'] and volume_ratio < 0.9
        else:  # 卖出信号
            if price['close'] >= pre_price['close']:  # 股价上涨，成交量不应缩小
                return price['volume'] < pre_price['volume'] and volume_ratio < 1.0
            else:  # 股价下跌，成交量应同步缩小
                return price['volume'] >= pre_price['volume'] and volume_ratio < 0.9


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
            # 股价上涨且 OBV 上升，确认买入信号
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

        # 获取前一个价格信息
        pre_price = df.iloc[-2]
        close_price = price['close']
        pre_close_price = pre_price['close']

        # 输出调试信息，帮助分析
        print(
            f'{stock["code"]}: latest_adosc={latest_adosc}, pre_adosc={pre_adosc}, close_price={close_price}, pre_close_price={pre_close_price}')

        # 确认股价与 ADOSC 是否同步
        if close_price > pre_close_price and latest_adosc > pre_adosc:
            trend_confirmed = True  # 股价和 ADOSC 同步上涨
        elif close_price < pre_close_price and latest_adosc < pre_adosc:
            trend_confirmed = True  # 股价和 ADOSC 同步下跌
        else:
            trend_confirmed = False  # 股价和 ADOSC 不一致，存在背离

        # 判断买入信号
        if self.signal == 1:
            if trend_confirmed:
                return latest_adosc > 0  # 股价和 ADOSC 同时上涨，确认买入
            else:
                return False  # 背离时不生成买入信号

        # 判断卖出信号
        else:
            if trend_confirmed:
                return True  # 股价和 ADOSC 同时下跌，确认卖出
            else:
                return False  # 背离时不生成卖出信号


class VWAP:
    label = 'VWAP'
    weight = 1

    def __init__(self, signal=1, volume_lookback=5):
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
            action = "买入"
            # 买入信号：股价上穿 VWAP 且量能支持
            price_cross = (close_pre_price < vwap_yesterday) and (close_price > vwap_today)
            result = price_cross and volume_confirm
        else:
            action = "卖出"
            # 卖出信号：股价下穿 VWAP 且量能支持
            price_cross = (close_pre_price > vwap_yesterday) and (close_price < vwap_today)
            result = price_cross and volume_confirm

        print(f"{stock['code']} VWAP 信号 = {result}（{action}），价格穿越 = {price_cross}，量能放大 = {volume_confirm}")
        return result


def get_up_volume_patterns():
    """
    获取成交量模式列表。

    Returns:
        list: 包含一个成交量模式对象的列表。
    """
    return [OBV(1), ADOSC(1), VWAP(1)]


def get_down_volume_patterns():
    """
    获取成交量模式列表。

    Returns:
        list: 包含一个成交量模式对象的列表。
    """
    return [OBV(-1), ADOSC(-1), VWAP(-1)]
