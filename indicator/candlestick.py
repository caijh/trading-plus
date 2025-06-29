import pandas_ta as ta

ALL_PATTERNS = [
    "2crows", "3blackcrows", "3inside", "3linestrike", "3outside", "3starsinsouth",
    "3whitesoldiers", "abandonedbaby", "advanceblock", "belthold", "breakaway",
    "closingmarubozu", "concealbabyswall", "counterattack", "darkcloudcover",
    "dojistar", "dragonflydoji", "engulfing", "eveningdojistar", "eveningstar",
    "gapsidesidewhite", "gravestonedoji", "hammer", "hangingman", "harami",
    "haramicross", "highwave", "hikkake", "hikkakemod", "homingpigeon",
    "identical3crows", "inneck", "inside", "invertedhammer", "kicking", "kickingbylength",
    "ladderbottom", "longleggeddoji", "longline", "marubozu", "matchinglow", "mathold",
    "morningdojistar", "morningstar", "onneck", "piercing", "rickshawman",
    "risefall3methods", "separatinglines", "shootingstar", "shortline", "spinningtop",
    "stalledpattern", "sticksandwich", "takuri", "tasukigap", "thrusting", "tristar",
    "unique3river", "upsidegap2crows", "xsidegap3methods"
]


class Candlestick:
    name = ''
    column = ''
    label = ''
    signal = 1
    weight = 1

    def __init__(self, name, label_, column, signal):
        self.signal = signal
        self.name = name
        self.label = label_
        self.column = column

    def match(self, stock, prices, df):
        """
        判断给定股票的最近几个交易日中是否出现了特定的K线形态。

        :param stock: 股票代码，用于标识特定的股票。
        :param prices: 股票价格数据，通常包括开、高、低、收等价格信息。
        :param df: 包含股票历史数据的DataFrame，至少包括['open', 'high', 'low', 'close']四个列。
        :return: 布尔值，表示是否匹配到了指定的K线形态。
        """
        # 获取最近几个交易日的数据，以便进行K线形态识别
        recent_df = df.tail(7)

        # 使用技术分析库ta，计算指定K线形态
        recent_df = ta.cdl_pattern(recent_df['open'], recent_df['high'], recent_df['low'], recent_df['close'],
                                   name=self.name)

        # 筛选出符合特定K线形态的行，即该列的值大于0
        if self.signal == 1:
            pattern = recent_df[recent_df[self.column] > 0]
        else:
            pattern = recent_df[recent_df[self.column] < 0]
        # 如果存在匹配的K线形态，则返回True，否则返回False
        result = not pattern.empty
        return result


def get_bullish_candlestick_patterns():
    """
    创建并返回一系列蜡烛图形态的实例列表。

    这个函数负责初始化并返回一个列表，列表中包含了不同类型的蜡烛图形态实例。
    这些形态实例包括锤头、十字星、看涨吞没、刺透和上升窗口等形态。
    """
    patterns = []
    for PATTERN in ALL_PATTERNS:
        patterns.append(Candlestick(PATTERN, PATTERN, f'CDL_{PATTERN.upper()}', 1))

    return patterns


def get_bearish_candlestick_patterns():
    """
    创建并返回一系列蜡烛图形态的实例列表。

    这个函数负责初始化并返回一个列表，列表中包含了看跌形态的蜡烛图形态实例。
    """
    patterns = []
    for PATTERN in ALL_PATTERNS:
        patterns.append(Candlestick(PATTERN, PATTERN, f'CDL_{PATTERN.upper()}', -1))

    return patterns
