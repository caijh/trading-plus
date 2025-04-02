import pandas_ta as ta


class Candlestick:
    name = ''
    column = ''
    label = ''

    def __init__(self, name, label, column):
        self.name = name
        self.label = label
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
        recent_df = df.tail(5)

        # 使用技术分析库ta，计算指定K线形态
        recent_df = ta.cdl_pattern(recent_df['open'], recent_df['high'], recent_df['low'], recent_df['close'],
                                   name=self.name)

        # 筛选出符合特定K线形态的行，即该列的值大于0
        pattern = recent_df[recent_df[self.column] > 0]
        # 如果存在匹配的K线形态，则返回True，否则返回False
        return not pattern.empty


def get_bullish_candlestick_patterns():
    """
    创建并返回一系列蜡烛图形态的实例列表。

    这个函数负责初始化并返回一个列表，列表中包含了不同类型的蜡烛图形态实例。
    这些形态实例包括锤头、十字星、看涨吞没、刺透和上升窗口等形态。
    """
    return [
        Candlestick('hammer', '锤子线', 'CDL_HAMMER'),
        Candlestick('morningdojistar', '十字晨星', 'CDL_MORNINGDOJISTAR'),
        Candlestick('morningstar', '晨星', 'CDL_MORNINGSTAR'),
        Candlestick('piercing', '刺透形态', 'CDL_PIERCING'),
        Candlestick('takuri', '探水杆', 'CDL_TAKURI'),
        Candlestick('engulfing', '看涨吞没', 'CDL_ENGULFING'),
        Candlestick('3whitesoldiers', '三白兵', 'CDL_3WHITESOLDIERS'),
        Candlestick('harami', '孕线', 'CDL_HARAMI'),
        Candlestick('haramicross', '十字孕线', 'CDL_HARAMICROSS'),
        Candlestick('breakaway', '突破形态', 'CDL_BREAKAWAY'),
        Candlestick('gapsidesidewhite', '缺口', 'CDL_GAPSIDESIDEWHITE'),
    ]
