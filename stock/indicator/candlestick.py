import pandas_ta as ta


class Candlestick:
    name = ''
    column = ''
    label = ''
    signal = 1

    def __init__(self, name, label, column, signal):
        self.name = name
        self.label = label
        self.column = column
        self.signal = signal

    def match(self, stock, prices, df):
        """
        判断给定股票的最近几个交易日中是否出现了特定的K线形态。

        :param stock: 股票代码，用于标识特定的股票。
        :param prices: 股票价格数据，通常包括开、高、低、收等价格信息。
        :param df: 包含股票历史数据的DataFrame，至少包括['open', 'high', 'low', 'close']四个列。
        :return: 布尔值，表示是否匹配到了指定的K线形态。
        """
        # 获取最近几个交易日的数据，以便进行K线形态识别
        recent_df = df.tail(5)

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
        print(f"{stock['code']} {'看跌' if self.signal != 1 else '看涨'}形态-{self.label} 是否出现: {result}")
        return result


def get_bullish_candlestick_patterns():
    """
    创建并返回一系列蜡烛图形态的实例列表。

    这个函数负责初始化并返回一个列表，列表中包含了不同类型的蜡烛图形态实例。
    这些形态实例包括锤头、十字星、看涨吞没、刺透和上升窗口等形态。
    """
    return [
        Candlestick('hammer', '锤子线', 'CDL_HAMMER', 1),
        Candlestick('invertedhammer', '倒锤子线', 'CDL_INVERTEDHAMMER', 1),
        Candlestick('morningstar', '晨星', 'CDL_MORNINGSTAR', 1),
        Candlestick('morningdojistar', '十字晨星', 'CDL_MORNINGDOJISTAR', 1),
        Candlestick('takuri', '探水杆', 'CDL_TAKURI', 1),
        Candlestick('3whitesoldiers', '三白兵', 'CDL_3WHITESOLDIERS', 1),
        Candlestick('matchinglow', '匹配低点', 'CDL_MATCHINGLOW', 1),
        Candlestick('ladderbottom', '阶梯底部', 'CDL_LADDERBOTTOM', 1),
        Candlestick('piercing', '刺透形态', 'CDL_PIERCING', 1),
        Candlestick('mathold', '持续形态', 'CDL_MATHOLD', 1),
        Candlestick('sticksandwich', '三明治形态', 'CDL_STICKSANDWICH', 1),
        Candlestick('engulfing', '看涨吞没', 'CDL_ENGULFING', 1),
        Candlestick('harami', '孕线', 'CDL_HARAMI', 1),
        Candlestick('haramicross', '十字孕线', 'CDL_HARAMICROSS', 1),
        Candlestick('breakaway', '突破形态', 'CDL_BREAKAWAY', 1),
        Candlestick('counterattack', '反击线', 'CDL_COUNTERATTACK', 1),
        Candlestick('tristar', '三颗星形态', 'CDL_TRISTAR', 1),
    ]


def get_bearish_candlestick_patterns():
    """
    创建并返回一系列蜡烛图形态的实例列表。

    这个函数负责初始化并返回一个列表，列表中包含了看跌形态的蜡烛图形态实例。
    """
    return [
        Candlestick('shootingstar', '流星形态', 'CDL_SHOOTINGSTAR', -1),
        Candlestick('hangingman', '上吊线', 'CDL_HANGINGMAN', -1),
        Candlestick('eveningstar', '黄晕星', 'CDL_EVENINGSTAR', -1),
        Candlestick('eveningdojistar', '十字黄晕星', 'CDL_EVENINGDOJISTAR', -1),
        Candlestick('darkcloudcover', '乌云盖顶', 'CDL_DARKCLOUDCOVER', -1),
        Candlestick('3blackcrows', '三只黑乌鸦', 'CDL_3BLACKCROWS', -1),
        Candlestick('advanceblock', '递进块形态', 'CDL_ADVANCEBLOCK', -1),
        Candlestick('identical3crows', '三只相同乌鸦', 'CDL_IDENTICAL3CROWS', -1),
        Candlestick('concealbabyswall', '隐藏婴儿吞没', 'CDL_CONCEALBABYSWALL', -1),
        Candlestick('onneck', '颈上线', 'CDL_ONNECK', -1),
        Candlestick('inneck', '颈内线', 'CDL_INNECK', -1),
        Candlestick('risefall3methods', '上升/下降三法', 'CDL_RISEFALL3METHODS', -1),
        Candlestick('engulfing', '看跌吞没', 'CDL_ENGULFING', -1),
        Candlestick('piercing', '刺透形态', 'CDL_PIERCING', -1),
        Candlestick('harami', '孕线', 'CDL_HARAMI', -1),
        Candlestick('haramicross', '十字孕线', 'CDL_HARAMICROSS', -1),
        Candlestick('breakaway', '突破形态', 'CDL_BREAKAWAY', -1),
        Candlestick('counterattack', '反击线', 'CDL_COUNTERATTACK', -1),
        Candlestick('tristar', '三颗星形态', 'CDL_TRISTAR', -1),

    ]
