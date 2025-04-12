from enum import Enum

import requests
import talib

from dataset.service import create_dataframe
from environment.service import env_vars
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
    # 尝试最多3次请求
    for attempt in range(3):
        try:
            # 发送GET请求并解析响应内容为JSON格式
            data = requests.get(url).json()
            # 检查响应状态码是否为0，表示请求成功
            if data['code'] == 0:
                # 提取并返回股票数据
                stock = data['data']
                return stock
        except requests.RequestException as e:
            print(f'Request failed: {e}. Retrying... {attempt + 1}')
    # 如果所有尝试都失败，返回None
    return None


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
        for attempt in range(3):
            try:
                data = requests.get(url).json()
                # 根据返回的数据检查状态码，如果为0表示请求成功，返回数据
                if data['code'] == 0:
                    return data['data']
                else:
                    print(data)
                    # 如果请求失败，返回空列表
                    return []
            except requests.RequestException as e:
                print(f'Request failed: {e}. Retrying...')
        # 如果所有尝试都失败，返回空列表
        return []
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
        if signal == 1:
            candlestick_patterns = get_bullish_candlestick_patterns()
            ma_patterns = get_up_ma_patterns()
            volume_patterns = get_up_volume_patterns()
        else:
            candlestick_patterns = get_bearish_candlestick_patterns()
            ma_patterns = get_down_ma_patterns()
            volume_patterns = get_down_volume_patterns()

        matched_candlestick_patterns = []
        matched_ma_patterns = []
        matched_volume_patterns = []
        df = create_dataframe(prices)
        candlestick_weight = 0
        for candlestick_pattern in candlestick_patterns:
            if candlestick_pattern.match(stock, prices, df):
                print(f'Stock {name} Match {candlestick_pattern.label}')
                candlestick_weight += candlestick_pattern.weight
                matched_candlestick_patterns.append(candlestick_pattern)

        min_candlestick_weight = 1 if signal == 1 else 0
        # 如果存在匹配的K线形态模式
        if candlestick_weight > min_candlestick_weight:
            # 初始化均线模式权重
            ma_weight = 0
            # 遍历所有均线模式
            for ma_pattern in ma_patterns:
                # 如果当前均线模式与股票数据匹配
                if ma_pattern.match(stock, prices, df):
                    # 打印匹配信息
                    print(f'Stock {name} Match {ma_pattern.label}')
                    # 将匹配的均线模式添加到列表中
                    matched_ma_patterns.append(ma_pattern)
                    # 累加当前均线模式的权重
                    ma_weight += ma_pattern.weight

            # 初始化量能模式权重
            volume_weight = 0
            # 遍历所有量能模式
            for volume_pattern in volume_patterns:
                # 如果当前量能模式与股票数据匹配
                if volume_pattern.match(stock, prices, df):
                    # 打印匹配信息
                    print(f'Stock {name} Match {volume_pattern.label}')
                    # 将匹配的量能模式添加到列表中
                    matched_volume_patterns.append(volume_pattern)
                    # 累加当前量能模式的权重
                    volume_weight += volume_pattern.weight

            # 如果信号为1，且均线和量能的权重都大于1
            if signal == 1:
                if ma_weight > 1 and volume_weight > 1:
                    # 将所有匹配的K线形态、均线和量能模式的标签添加到股票的模式列表中
                    for matched_candlestick_pattern in matched_candlestick_patterns:
                        stock['patterns'].append(matched_candlestick_pattern.label)
                    for matched_ma_pattern in matched_ma_patterns:
                        stock['patterns'].append(matched_ma_pattern.label)
                    for matched_volume_pattern in matched_volume_patterns:
                        stock['patterns'].append(matched_volume_pattern.label)
            # 如果信号不为1，但均线和量能的权重都大于0
            else:
                if ma_weight > 0 and volume_weight > 0:
                    # 同样将所有匹配的模式标签添加到股票的模式列表中
                    for matched_candlestick_pattern in matched_candlestick_patterns:
                        stock['patterns'].append(matched_candlestick_pattern.label)
                    for matched_ma_pattern in matched_ma_patterns:
                        stock['patterns'].append(matched_ma_pattern.label)
                    for matched_volume_pattern in matched_volume_patterns:
                        stock['patterns'].append(matched_volume_pattern.label)

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
