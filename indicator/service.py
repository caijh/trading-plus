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


def get_match_ma_patterns(patterns, stock, prices, df, volume_weight_limit=1):
    """
    根据给定的模式列表，筛选出与特定股票匹配的均线模式。

    参数:
    - patterns: 一个包含所有待检测模式的列表。
    - stock: 一个包含股票信息的字典，必须包含'code'和'name'键。
    - prices: 股票价格数据。
    - df: 包含股票数据的DataFrame。
    - volume_weight_limit=1: 体积权重的阈值，用于过滤模式。

    返回:
    - matched_ma_patterns: 与股票匹配的均线模式列表。
    - ma_weight: 匹配模式的总权重。
    - list(matched_volume_patterns): 匹配的成交量模式列表。
    """
    # 提取股票代码和名称
    code = stock['code']
    name = stock['name']

    # 初始化均线权重和匹配的均线模式列表
    ma_weight = 0
    matched_ma_patterns = []

    # 初始化匹配的成交量模式集合，避免重复计数
    matched_volume_patterns = set()
    matched_volume_pattern_labels = set()
    exec_matched_volume_pattern_labels = set()

    try:
        # 遍历所有模式，寻找匹配的均线模式
        for pattern in patterns:
            # 如果当前模式与股票匹配，则进一步检查成交量模式
            if pattern.match(stock, prices, df):
                # 获取当前模式对应的成交量确认模式
                volume_confirm_patterns = pattern.get_volume_confirm_patterns()

                volume_patterns = []
                total_volume_weight = 0
                total_volume_matched_patterns = []
                for volume_pattern in volume_confirm_patterns:
                    if volume_pattern.label not in exec_matched_volume_pattern_labels:
                        volume_patterns.append(volume_pattern)
                    else:
                        total_volume_matched_patterns.append(volume_pattern)
                        total_volume_weight += volume_pattern.weight


                # 检查成交量模式是否匹配，并获取匹配的模式和权重
                volume_matched_patterns, volume_weight = get_match_patterns(volume_patterns, stock, prices, df,
                                                                            'volume')
                for volume_pattern in volume_matched_patterns:
                    if volume_pattern.label not in exec_matched_volume_pattern_labels:
                        exec_matched_volume_pattern_labels.add(volume_pattern.label)
                    total_volume_matched_patterns.append(volume_pattern)

                total_volume_weight += volume_weight
                # 如果成交量权重超过阈值，则认为该模式有效
                if total_volume_weight > volume_weight_limit:
                    # 打印匹配信息
                    print(f'{code} {name} Match {pattern.label}')

                    # 累加当前模式的权重到总权重
                    ma_weight += pattern.weight

                    # 将当前模式添加到匹配的均线模式列表中
                    matched_ma_patterns.append(pattern)

                    # 将所有匹配的成交量模式标签添加到集合中
                    for volume_pattern in total_volume_matched_patterns:
                        if volume_pattern.label not in matched_volume_pattern_labels:
                            matched_volume_pattern_labels.add(volume_pattern.label)
                            matched_volume_patterns.add(volume_pattern)
    except Exception as e:
        # 捕获并打印任何异常，然后继续执行程序
        print(e)
        pass

    # 返回匹配的均线模式、总权重和匹配的成交量模式列表
    return matched_ma_patterns, ma_weight, list(matched_volume_patterns)


def get_match_patterns(patterns, stock, prices, df, pattern_type=''):
    code = stock['code']
    name = stock['name']
    weight = 0
    matched_patterns = []
    try:
        for pattern in patterns:
            if pattern.match(stock, prices, df):
                if pattern_type != 'volume':
                    print(f'{code} {name} Match {pattern.label}')
                weight += pattern.weight
                matched_patterns.append(pattern)
    except Exception as e:
        print(e)
    return matched_patterns, weight
