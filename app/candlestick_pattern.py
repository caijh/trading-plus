import pandas_ta as ta


class CandlestickPattern:
    name = ''
    column = ''
    label = ''

    def __init__(self, name, label, column):
        self.name = name
        self.label = label
        self.column = column

    def match(self, stock, prices, df):
        recent_df = df.tail(5)
        recent_df = ta.cdl_pattern(recent_df['open'], recent_df['high'], recent_df['low'], recent_df['close'],
                                   name=self.name)
        pattern = recent_df[recent_df[self.column] != 0]
        return not pattern.empty


def get_candlestick_patterns():
    """
    创建并返回一系列蜡烛图形态的实例列表。

    这个函数负责初始化并返回一个列表，列表中包含了不同类型的蜡烛图形态实例。
    这些形态实例包括锤头、十字星、看涨吞没、刺透和上升窗口等形态。
    """
    return [
        CandlestickPattern('hammer', '锤子线', 'CDL_HAMMER'),
        CandlestickPattern('invertedhammer', '倒锤子线', 'CDL_INVERTEDHAMMER'),
        CandlestickPattern('morningdojistar', '十字晨星', 'CDL_MORNINGDOJISTAR'),
        CandlestickPattern('morningstar', '晨星', 'CDL_MORNINGSTAR'),
        CandlestickPattern('piercing', '刺透形态', 'CDL_PIERCING'),
        CandlestickPattern('takuri', '探水杆', 'CDL_TAKURI'),
        CandlestickPattern('engulfing', '看涨吞没', 'CDL_ENGULFING'),
        CandlestickPattern('3whitesoldiers', '三白兵', 'CDL_3WHITESOLDIERS'),
        CandlestickPattern('harami', '孕线', 'CDL_HARAMI'),
        CandlestickPattern('haramicross', '十字孕线', 'CDL_HARAMICROSS'),
        CandlestickPattern('breakaway', '突破形态', 'CDL_BREAKAWAY'),
    ]
