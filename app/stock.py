from enum import Enum

import requests

from candlestick_pattern import get_candlestick_patterns
from dataset import create_dataframe
from env import env_vars
from ma_pattern import get_ma_patterns
from predictor import predict_and_plot
from volume_pattern import get_volume_patterns


class KType(Enum):
    DAY = 'D'


def get_stock(code):
    url = f'{env_vars.TRADING_DATA_URL}/stock?code={code}'
    data = requests.get(url).json()
    if data['code'] == 0:
        stock = data['data']
        return stock
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
        data = requests.get(url).json()
        # 根据返回的数据检查状态码，如果为0表示请求成功，返回数据
        if data['code'] == 0:
            return data['data']
        else:
            print(data)
            # 如果请求失败，返回空列表
            return []
    # 如果k_type不是DAY，直接返回空列表，表示不支持的k_type
    return []


def analyze_stock(stock, k_type=KType.DAY):
    code = stock['code']
    name = stock['name']
    stock['patterns'] = []
    stock['predict_price'] = None
    prices = get_stock_price(code, k_type)
    if not prices:
        return stock
    else:
        print(f'Analyzing Stock, code = {code}, name = {name}')
        candlestick_patterns = get_candlestick_patterns()
        ma_patterns = get_ma_patterns()
        volume_patterns = get_volume_patterns()
        matched_candlestick_patterns = []
        matched_ma_patterns = []
        matched_volume_patterns = []
        df = create_dataframe(prices)
        for candlestick_pattern in candlestick_patterns:
            if candlestick_pattern.match(stock, prices, df):
                print(f'Stock {name} Match {candlestick_pattern.label}')
                matched_candlestick_patterns.append(candlestick_pattern.label)

        if len(matched_candlestick_patterns) != 0:
            for ma_pattern in ma_patterns:
                if ma_pattern.match(stock, prices, df):
                    print(f'Stock {name} Match {ma_pattern.name()}')
                    matched_ma_patterns.append(ma_pattern.name())
            for volume_pattern in volume_patterns:
                if volume_pattern.match(stock, prices, df):
                    print(f'Stock {name} Match {volume_pattern.name()}')
                    matched_volume_patterns.append(volume_pattern.name())

        if (len(matched_candlestick_patterns) != 0
                and len(matched_ma_patterns) > 1 and len(matched_volume_patterns) != 0):
            for matched_candlestick_pattern in matched_candlestick_patterns:
                stock['patterns'].append(matched_candlestick_pattern)
            for matched_ma_pattern in matched_ma_patterns:
                stock['patterns'].append(matched_ma_pattern)
            for matched_volume_pattern in matched_volume_patterns:
                stock['patterns'].append(matched_volume_pattern)

            predict_prices = predict_and_plot(stock, prices, 7)
            stock['predict_price'] = round(float(predict_prices[0]), 2)
    print(
        f'Analyzing Complete code = {code}, name = {name}, patterns = {stock["patterns"]}, predict_price = {stock["predict_price"]}')
    return stock
