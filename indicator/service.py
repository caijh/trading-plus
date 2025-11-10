from indicator.adl import ADL
from indicator.adoc import ADOSC
from indicator.adx import ADX
from indicator.ar import AR
from indicator.aroon import AROON
from indicator.bias import BIAS
from indicator.candlestick import get_bullish_candlestick_patterns, get_bearish_candlestick_patterns
from indicator.chaikin import Chaikin
from indicator.cmf import CMF
from indicator.kdj import KDJ
from indicator.kvo import KVO
from indicator.macd import MACD
from indicator.mfi import MFI
from indicator.nvi import NVI
from indicator.obv import OBV
from indicator.pvi import PVI
from indicator.rsi import RSI
from indicator.sar import SAR
from indicator.sma import SMA
from indicator.vpt import VPT
from indicator.wr import WR


def get_candlestick_signal(stock, df, candlestick_weight):
    """
    根据K线形态匹配结果生成交易信号

    参数:
        stock: 股票代码
        df: 包含K线数据的DataFrame
        candlestick_weight: K线形态权重阈值

    返回值:
        tuple: (信号值, 匹配的形态列表)
               信号值：-1表示看跌信号，1表示看涨信号，0表示无信号
               匹配的形态列表：符合权重阈值的K线形态名称列表
    """
    # 检查是否存在看跌K线形态
    bearish_matched_patterns, bearish_weight = get_match_patterns(get_bearish_candlestick_patterns(), stock, df,
                                                                  trending=None, direction=None)
    bullish_matched_patterns, bullish_weight = get_match_patterns(get_bullish_candlestick_patterns(), stock, df,
                                                                  trending=None, direction=None)
    if bearish_weight > bullish_weight >= candlestick_weight:
        return -1, bearish_matched_patterns

    if bullish_weight > bearish_weight >= candlestick_weight:
        return 1, bullish_matched_patterns

    if bullish_weight == bearish_weight >= candlestick_weight:
        bearish_matched_pattern = max(bearish_matched_patterns, key=lambda x: x.weight)
        bullish_matched_pattern = max(bullish_matched_patterns, key=lambda x: x.weight)
        if bearish_matched_pattern.weight > bullish_matched_pattern.weight:
            return -1, bearish_matched_patterns
        if bearish_matched_pattern.weight < bullish_matched_pattern.weight:
            return 1, bullish_matched_patterns

    # 无明显信号时返回默认值
    return 0, []


def get_indicator_signal(stock, df, trending, direction, ma_weight_limit, volume_weight_limit):
    """
    获取股票技术指标信号

    参数:
        stock: 股票代码
        df: 股票数据DataFrame
        trending: 趋势状态
        direction: 方向参数
        ma_weight_limit: 移动平均权重限制
        volume_weight_limit: 成交量权重限制

    返回值:
        tuple: (信号值, 匹配的主要模式列表, 匹配的次要模式列表)
               信号值：-1表示卖出信号，1表示买入信号，0表示无信号
    """
    # 检查下跌模式信号
    patterns = get_down_primary_patterns()

    matched_patterns, weight = get_match_patterns(patterns, stock, df, trending, direction)
    matched_secondary_patterns = []
    if weight >= ma_weight_limit:
        patterns = get_down_secondary_patterns()
        matched_secondary_patterns, weight = get_match_patterns(patterns, stock, df, trending, direction)
        if weight >= volume_weight_limit:
            return -1, matched_patterns, matched_secondary_patterns

    # 检查上涨模式信号
    patterns = get_up_primary_patterns()
    matched_patterns, weight = get_match_patterns(patterns, stock, df, trending, direction)

    if weight >= ma_weight_limit:
        patterns = get_up_secondary_patterns()
        matched_secondary_patterns, weight = get_match_patterns(patterns, stock, df, trending, direction)
        if weight >= volume_weight_limit:
            return 1, matched_patterns, matched_secondary_patterns

    return 0, matched_patterns, matched_secondary_patterns


def get_up_primary_patterns():
    """
    创建并返回一个包含常用均线和偏差率模式的列表。

    这个函数初始化了一个列表，包含了不同周期的均线（如5日、10日、20日、60日、200日均线），
    以及一个特定参数的偏差率模式。这些模式用于在金融数据分析中计算和应用各种移动平均线和偏差率指标。
    """
    # 初始化均线和偏差率模式列表
    patterns = [
        SMA(10, 1),
        SMA(20, 1),
        SMA(50, 1),
        MACD(1),
        SAR(1),
        BIAS(20, -0.09, 1),
        KDJ(1),
        RSI(1),
        WR(1)
    ]
    return patterns


def get_down_primary_patterns():
    """
    创建并返回一个包含常用均线和偏差率模式的列表。

    这个函数初始化了一个列表，包含了不同周期的均线（如5日、10日、20日、60日、200日均线），
    以及一个特定参数的偏差率模式。这些模式用于在金融数据分析中计算和应用各种移动平均线和偏差率指标。
    """
    # 初始化均线和偏差率
    patterns = [
        SMA(10, -1),
        SMA(20, -1),
        SMA(50, -1),
        MACD(-1),
        SAR(-1),
        BIAS(20, 0.09, -1),
        KDJ(-1),
        RSI(-1),
        WR(-1)
    ]
    return patterns


def get_up_secondary_patterns():
    return [
        ADL(1),
        ADOSC(1),
        ADX(1),
        AR(1),
        AROON(1),
        Chaikin(1),
        CMF(1),
        MFI(1),
        KVO(1),
        NVI(1),
        OBV(1),
        PVI(1),
        VPT(1),
    ]


def get_down_secondary_patterns():
    return [
        ADL(-1),
        ADOSC(-1),
        ADX(-1),
        AR(-1),
        AROON(-1),
        Chaikin(-1),
        CMF(-1),
        MFI(-1),
        KVO(-1),
        NVI(-1),
        OBV(-1),
        PVI(-1),
        VPT(-1),
    ]


def get_match_ma_patterns(patterns, stock, df, trending, direction, volume_weight_limit=1):
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
            if pattern.match(stock, df, trending, direction):
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
                volume_matched_patterns, volume_weight = get_match_patterns(volume_patterns, stock, df, trending,
                                                                            direction)
                for volume_pattern in volume_matched_patterns:
                    if volume_pattern.label not in exec_matched_volume_pattern_labels:
                        exec_matched_volume_pattern_labels.add(volume_pattern.label)
                    total_volume_matched_patterns.append(volume_pattern)

                total_volume_weight += volume_weight
                # 如果成交量权重超过阈值，则认为该模式有效
                if total_volume_weight >= volume_weight_limit:
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

    # 返回匹配的均线模式、总权重和匹配的成交量模式列表
    return matched_ma_patterns, ma_weight, list(matched_volume_patterns)


def get_match_patterns(patterns, stock, df, trending, direction):
    weight = 0
    matched_patterns = []
    try:
        for pattern in patterns:
            if pattern.match(stock, df, trending, direction):
                print(f'{stock['code']} {stock['name']} Match {pattern.label}')
                weight += pattern.weight
                matched_patterns.append(pattern)
    except Exception as e:
        print(e)
    return matched_patterns, weight


def get_exit_patterns():
    return [KDJ(-1), RSI(-1), WR(-1)]
