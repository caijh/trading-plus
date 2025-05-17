from indicator.candlestick import get_bullish_candlestick_patterns, get_bearish_candlestick_patterns
from indicator.ma import get_up_ma_patterns, get_down_ma_patterns


def get_patterns(signal):
    """
    根据信号获取相应的K线模式、均线模式和成交量模式。

    本函数根据输入的signal值（1或非1），来决定市场是处于上升趋势还是下降趋势，
    然后分别调用对应的函数获取K线模式、均线模式和成交量模式。

    参数:
    signal (int): 市场信号，1代表买入信号，非1代表卖出信号。

    返回:
    tuple: 包含三个元素的元组，分别是K线模式列表、均线模式列表。
    """
    # 根据信号判断市场趋势并获取相应的模式
    if signal == 1:
        # 买入信号的模式
        candlestick_patterns = get_bullish_candlestick_patterns()
        ma_patterns = get_up_ma_patterns()
    else:
        # 卖出信号的模式
        candlestick_patterns = get_bearish_candlestick_patterns()
        ma_patterns = get_down_ma_patterns()

    # 返回获取到的模式
    return candlestick_patterns, ma_patterns


def get_volume_patterns(matched_ma_patterns):
    patterns = []
    pattern_labels = []
    for pattern in matched_ma_patterns:
        volume_patterns = pattern.get_volume_confirm_patterns()
        for volume_pattern in volume_patterns:
            pattern_label = f'${volume_pattern.label}_${volume_pattern.signal}'
            if pattern_label not in pattern_labels:
                patterns.append(volume_pattern)
                pattern_labels.append(pattern_label)

    return patterns


def get_match_patterns(patterns, stock, prices, df):
    code = stock['code']
    name = stock['name']
    weight = 0
    matched_patterns = []
    try:
        for pattern in patterns:
            if pattern.match(stock, prices, df):
                print(f'{code} {name} Match {pattern.label}')
                weight += pattern.weight
                matched_patterns.append(pattern)
    except Exception as e:
        print(e)
        pass
    return matched_patterns, weight
