from app.core.logger import logger
from app.indicator.primary.bias import BIAS
from app.indicator.primary.candlestick import get_bullish_candlestick_patterns, get_bearish_candlestick_patterns
from app.indicator.primary.kdj import KDJ
from app.indicator.primary.macd import MACD
from app.indicator.primary.rsi import RSI
from app.indicator.primary.sma import SMA
from app.indicator.primary.wr import WR
from app.indicator.secondary.adl import ADL
from app.indicator.secondary.adoc import ADOSC
from app.indicator.secondary.adx import ADX
from app.indicator.secondary.ar import AR
from app.indicator.secondary.aroon import AROON
from app.indicator.secondary.chaikin import Chaikin
from app.indicator.secondary.cmf import CMF
from app.indicator.secondary.kvo import KVO
from app.indicator.secondary.mfi import MFI
from app.indicator.secondary.nvi import NVI
from app.indicator.secondary.obv import OBV
from app.indicator.secondary.pvi import PVI
from app.indicator.secondary.vpt import VPT


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


def get_indicator_patterns(stock, df, trending, direction, primary_patterns, secondary_patterns):
    matched_patterns, ma_weight = get_match_patterns(primary_patterns, stock, df, trending, direction)
    matched_secondary_patterns, volume_weight = get_match_patterns(secondary_patterns, stock, df, trending, direction)
    return ma_weight, volume_weight, matched_patterns, matched_secondary_patterns


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
    down_weight, volume_weight, down_matched_patterns, down_matched_secondary_patterns = get_indicator_patterns(stock,
                                                                                                                df,
                                                                                                                trending,
                                                                                                                direction,
                                                                                                                get_down_primary_patterns(),
                                                                                                                get_down_secondary_patterns())

    up_weight, volume_weight, up_matched_patterns, up_matched_secondary_patterns = get_indicator_patterns(stock, df,
                                                                                                          trending,
                                                                                                          direction,
                                                                                                          get_up_primary_patterns(),
                                                                                                          get_up_secondary_patterns())

    if up_weight > down_weight and up_weight >= ma_weight_limit and volume_weight >= volume_weight_limit:
        return 1, up_matched_patterns, up_matched_secondary_patterns
    if down_weight > up_weight and down_weight >= ma_weight_limit and volume_weight >= volume_weight_limit:
        return -1, down_matched_patterns, down_matched_secondary_patterns

    return 0, [], []


def get_up_primary_patterns():
    """
    创建并返回一个包含常用均线和偏差率模式的列表。

    这个函数初始化了一个列表，包含了不同周期的均线（如5日、10日、20日、60日、120日均线），
    以及一个特定参数的偏差率模式。这些模式用于在金融数据分析中计算和应用各种移动平均线和偏差率指标。
    """
    # 初始化均线和偏差率模式列表
    patterns = [
        SMA(10, 1),
        SMA(20, 1),
        SMA(50, 1),
        SMA(120, 1),
        MACD(1),
        # SAR(1),
        BIAS(20, -0.09, 1),
        KDJ(1),
        RSI(1),
        WR(1)
    ]
    return patterns


def get_down_primary_patterns():
    """
    创建并返回一个包含常用均线和偏差率模式的列表。

    这个函数初始化了一个列表，包含了不同周期的均线（如5日、10日、20日、60日、120日均线），
    以及一个特定参数的偏差率模式。这些模式用于在金融数据分析中计算和应用各种移动平均线和偏差率指标。
    """
    # 初始化均线和偏差率
    patterns = [
        SMA(10, -1),
        SMA(20, -1),
        SMA(50, -1),
        SMA(120, -1),
        MACD(-1),
        # SAR(-1),
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


def get_match_patterns(patterns, stock, df, trending, direction):
    weight = 0
    matched_patterns = []
    try:
        for pattern in patterns:
            if pattern.match(stock, df, trending, direction):
                logger.info(f'{stock['code']} {stock['name']} Match {pattern.label}')
                weight += pattern.weight
                matched_patterns.append(pattern)
    except Exception as e:
        logger.info(e, exc_info=True)
    return matched_patterns, weight


def get_exit_patterns():
    return [KDJ(-1), RSI(-1), WR(-1)]
