from enum import Enum

import requests

from candlestick_pattern import get_candlestick_patterns
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
    if k_type == KType.DAY:
        price_url = f'{env_vars.TRADING_DATA_URL}/stock/price/daily?code={code}'
        data = requests.get(price_url).json()
        if data['code'] == 0:
            return data['data']
        else:
            return []
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
        print(f'Analyzing... code = {code}, name = {name}')
        candlestick_patterns = get_candlestick_patterns()
        ma_patterns = get_ma_patterns()
        volume_patterns = get_volume_patterns()
        matched_candlestick_patterns = []
        matched_ma_patterns = []
        matched_volume_patterns = []
        for candlestick_pattern in candlestick_patterns:
            if candlestick_pattern.match(stock, prices):
                matched_candlestick_patterns.append(candlestick_pattern.name())

        if len(matched_candlestick_patterns) != 0:
            for ma_pattern in ma_patterns:
                if ma_pattern.match(stock, prices):
                    matched_ma_patterns.append(ma_pattern.name())
            for volume_pattern in volume_patterns:
                if volume_pattern.match(stock, prices):
                    matched_volume_patterns.append(volume_pattern.name())

        if (len(matched_candlestick_patterns) != 0
                and len(matched_ma_patterns) != 0 and len(matched_volume_patterns) != 0):
            for matched_candlestick_pattern in matched_candlestick_patterns:
                stock['patterns'].append(matched_candlestick_pattern)
            for matched_ma_pattern in matched_ma_patterns:
                stock['patterns'].append(matched_ma_pattern)
            for matched_volume_pattern in matched_volume_patterns:
                stock['patterns'].append(matched_volume_pattern)

            predict_prices = predict_and_plot(stock, prices, 20)
            stock['predict_price'] = round(float(predict_prices[0]), 2)
    print(
        f'Analyzing Complete code = {code}, name = {name}, patterns = {stock["patterns"]}, predict_price = {stock["predict_price"]}')
    return stock
