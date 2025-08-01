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
    recent = 5

    def __init__(self, name, label_, column, signal):
        self.signal = signal
        self.name = name
        self.label = label_
        self.column = column

    def match(self, stock, prices, df):
        """
        判断给定股票的最近几个交易日中是否出现了特定的K线形态，并记录出现的日期。

        :param stock: 股票字典，将在其中记录形态出现的日期。
        :param prices: 股票价格数据（未使用，但保留参数结构）。
        :param df: 包含股票历史数据的DataFrame，至少包括['open', 'high', 'low', 'close']列。
        :return: 布尔值，表示是否匹配到了指定的K线形态。
        """
        # 用最近20根K线计算形态
        pattern_df = df.tail(20).copy()

        # 计算K线形态，结果列为 self.column
        pattern_df[self.column] = ta.cdl_pattern(
            pattern_df['open'], pattern_df['high'], pattern_df['low'], pattern_df['close'], name=self.name
        )

        # 检查最近 self.recent 根K线是否匹配信号
        recent_pattern = pattern_df.tail(self.recent)

        if self.signal == 1:
            matched = recent_pattern[recent_pattern[self.column] > 0]
        else:
            matched = recent_pattern[recent_pattern[self.column] < 0]

        # 提取匹配日期，并写入 stock 中
        if not matched.empty:
            candlestick_patterns = {
                'name': self.name,
                'dates': matched.index.strftime('%Y-%m-%d').tolist()
            }
            stock['patterns_candlestick'].append(candlestick_patterns)
            return True
        else:
            return False


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
