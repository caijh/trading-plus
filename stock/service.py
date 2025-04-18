from enum import Enum

import talib

from dataset.service import create_dataframe
from environment.service import env_vars
from request.service import http_get_with_retries
from stock.indicator.candlestick import get_bullish_candlestick_patterns, get_bearish_candlestick_patterns
from stock.indicator.ma import get_up_ma_patterns, get_down_ma_patterns
from stock.indicator.volume import get_up_volume_patterns, get_down_volume_patterns


class KType(Enum):
    DAY = 'D'


def get_stock(code):
    """
    根据股票代码获取股票信息。

    通过发送HTTP GET请求到TRADING_DATA_URL获取股票数据，如果请求成功，
    则解析并返回股票信息，否则返回None。

    参数:
    code (str): 股票代码，用于唯一标识一个股票。

    返回:
    stock: 如果请求成功且数据有效，则返回股票信息，否则返回None。
    """
    # 构造请求URL，包含股票代码
    url = f'{env_vars.TRADING_DATA_URL}/stock?code={code}'
    return http_get_with_retries(url, 3, None)


def get_stock_price(code, k_type=KType.DAY):
    """
    根据股票代码和K线类型获取股票价格数据。

    参数:
    code (str): 股票代码，用于标识特定的股票。
    k_type (KType): K线类型，默认为日K线。这决定了返回的价格数据的时间周期。

    返回:
    list: 如果请求成功，返回包含股票价格数据的列表；如果请求失败或不支持的k_type，则返回空列表。
    """
    # 当请求的是日K线数据时，构造请求URL并发送请求
    if k_type == KType.DAY:
        url = f'{env_vars.TRADING_DATA_URL}/stock/price/daily?code={code}'
        print(f'Get stock price from {url} , code = {code}, k_type = {k_type}')
        return http_get_with_retries(url, 3, [])
    # 如果k_type不是DAY，直接返回空列表，表示不支持的k_type
    return []


def analyze_stock(stock, k_type=KType.DAY, signal=1):
    code = stock['code']
    name = stock['name']
    stock['patterns'] = []
    stock['predict_price'] = None
    prices = get_stock_price(code, k_type)
    if not prices:
        print(f'No prices get for  stock {code}')
        return stock
    else:
        print(f'Analyzing Stock, code = {code}, name = {name}')
        candlestick_patterns, ma_patterns, volume_patterns = get_patterns(signal)

        df = create_dataframe(prices)

        matched_candlestick_patterns, candlestick_weight = get_match_patterns(candlestick_patterns, stock, prices, df)

        # 买入，需要满足k线形态大于1，卖出，k线形态需要满足大于0
        min_candlestick_weight = 1 if signal == 1 else 0
        # 如果存在匹配的K线形态模式
        if candlestick_weight > min_candlestick_weight:
            matched_ma_patterns, ma_weight = get_match_patterns(ma_patterns, stock, prices, df)
            matched_volume_patterns, volume_weight = get_match_patterns(volume_patterns, stock, prices, df)

            # 如果信号为1，且均线和量能的权重都大于1
            if signal == 1:
                if ma_weight > 1 and volume_weight > 1:
                    # 将所有匹配的K线形态、均线和量能模式的标签添加到股票的模式列表中
                    append_matched_pattern_label(matched_candlestick_patterns, stock)
                    append_matched_pattern_label(matched_ma_patterns, stock)
                    append_matched_pattern_label(matched_volume_patterns, stock)
            # 如果信号不为1，但均线和量能的权重都大于0
            else:
                if ma_weight > 0 and volume_weight > 0:
                    # 同样将所有匹配的模式标签添加到股票的模式列表中
                    append_matched_pattern_label(matched_candlestick_patterns, stock)
                    append_matched_pattern_label(matched_ma_patterns, stock)
                    append_matched_pattern_label(matched_volume_patterns, stock)

            # predict_prices = predict_and_plot(stock, prices, 7)
            # stock['predict_price'] = round(float(predict_prices[0]), 2)

        # 计算给定股票的支持位和阻力位
        # 参数:
        #   stock: 包含股票数据的字典或数据框，应包括历史价格等信息
        #   df: 用于计算支持位和阻力位的数据框，通常包含历史价格数据
        # 返回值:
        #   support: 计算得到的支持位价格
        #   resistance: 计算得到的阻力位价格
        (support, resistance) = cal_support_resistance(stock, df)

        # 将计算得到的支持位和阻力位添加到股票数据中
        stock['support'] = support
        stock['resistance'] = resistance

    print(
        f'Analyzing Complete code = {code}, name = {name}, patterns = {stock["patterns"]}, predict_price = {stock["predict_price"]}')
    return stock


def append_matched_pattern_label(matched_patterns, stock):
    """
    将匹配到的模式标签添加到股票信息中。

    遍历匹配到的模式列表，将每个模式的标签添加到指定的股票信息字典中的 'patterns' 键下。

    参数:
    matched_patterns: 匹配到的模式对象列表，每个模式对象包含一个 'label' 属性，用于表示模式的标签。
    stock: 包含股票信息的字典，必须包含一个 'patterns' 键，用于存储模式标签的列表。

    返回:
    无返回值。此函数直接修改传入的股票信息字典。
    """
    # 遍历匹配到的模式列表
    for matched_pattern in matched_patterns:
        # 将模式的标签添加到股票信息的 'patterns' 列表中
        stock['patterns'].append(matched_pattern.label)


def get_patterns(signal):
    """
    根据信号获取相应的K线模式、均线模式和成交量模式。

    本函数根据输入的signal值（1或非1），来决定市场是处于上升趋势还是下降趋势，
    然后分别调用对应的函数获取K线模式、均线模式和成交量模式。

    参数:
    signal (int): 市场信号，1代表上升趋势，非1代表下降趋势。

    返回:
    tuple: 包含三个元素的元组，分别是K线模式列表、均线模式列表和成交量模式列表。
    """
    # 根据信号判断市场趋势并获取相应的模式
    if signal == 1:
        # 上升趋势时的模式
        candlestick_patterns = get_bullish_candlestick_patterns()
        ma_patterns = get_up_ma_patterns()
        volume_patterns = get_up_volume_patterns()
    else:
        # 下降趋势时的模式
        candlestick_patterns = get_bearish_candlestick_patterns()
        ma_patterns = get_down_ma_patterns()
        volume_patterns = get_down_volume_patterns()

    # 返回获取到的三种模式
    return candlestick_patterns, ma_patterns, volume_patterns


def get_match_patterns(patterns, stock, prices, df):
    name = stock['name']
    weight = 0
    matched_patterns = []
    for pattern in patterns:
        if pattern.match(stock, prices, df):
            print(f'Stock {name} Match {pattern.label}')
            weight += pattern.weight
            matched_patterns.append(pattern)
    return matched_patterns, weight


def cal_support_resistance(stock, df):
    """
    计算给定股票的支撑位和阻力位。

    参数:
    - stock: 包含股票信息的字典，至少需要包含股票代码。
    - df: 包含股票历史数据的DataFrame，至少需要包含high, low, close列。

    返回:
    - s: 支撑位，计算结果四舍五入到两位小数。
    - r: 阻力位，计算结果四舍五入到两位小数。
    """
    # 计算 Pivot Points
    df['Pivot'] = (df['high'].shift(1) + df['low'].shift(1) + df['close'].shift(1)) / 3
    df['R1'] = 2 * df['Pivot'] - df['low'].shift(1)
    df['S1'] = 2 * df['Pivot'] - df['high'].shift(1)
    df['R2'] = df['Pivot'] + (df['high'].shift(1) - df['low'].shift(1))
    df['S2'] = df['Pivot'] - (df['high'].shift(1) - df['low'].shift(1))

    # 计算 Fractal 阻力 & 支撑
    df['Fractal_High'] = talib.MAX(df['high'], timeperiod=5)  # 5 天最高点
    df['Fractal_Low'] = talib.MIN(df['low'], timeperiod=5)  # 5 天最低点

    # 提取最新数据行，用于计算最终的支撑位和阻力位
    latest_data = df.iloc[-1][['Pivot', 'R1', 'R2', 'S1', 'S2', 'Fractal_Low', 'Fractal_High']]

    # 计算最终的支撑位和阻力位
    # s = round((latest_data['S1'] + latest_data['S2'] + latest_data['Fractal_Low']) / 3, 2)
    s = round((latest_data['S1'] + latest_data['S2']) / 2, 2)
    # r = round((latest_data['R1'] + latest_data['R2'] + latest_data['Fractal_High']) / 3, 2)
    r = round((latest_data['R1'] + latest_data['R2']) / 2, 2)

    # 打印计算结果
    print(f'Stock {stock["code"]} calculate Support = {s}, Resistance = {r}')

    return s, r
