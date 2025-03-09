from enum import Enum

import requests

from candlestick_pattern import get_candlestick_patterns
from env import env_vars
from ma_pattern import get_ma_patterns
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
    print(f'Analyzing stock... code = {code}, name = {name}')
    prices = get_stock_price(code, k_type)
    if not prices:
        return stock
    else:
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
    print(f'Analyzing complete patterns = {stock["patterns"]}')
    return stock
