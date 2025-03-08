from enum import Enum

import requests

from candlestick_pattern import get_candlestick_patterns
from env import env_vars


class KType(Enum):
    DAY = 'D'


def get_stock_price(code, k_type=KType.DAY):
    if k_type == KType.DAY:
        price_url = f'{env_vars.TRADING_DATA_URL}/stock/price/daily?code={code}'
        print(price_url)
        data = requests.get(price_url).json()
        if data['code'] == 0:
            return data['data']
        else:
            return []
    return []


def analyze_stock(stock, k_type=KType.DAY):
    code = stock['code']
    print(f'Start analysis {code}')
    prices = get_stock_price(code, k_type)
    if not prices:
        return None
    else:
        print(f'Analyzing stock price, name = {stock["name"]}, code = {code}')
        candlestick_patterns = get_candlestick_patterns()
        for candlestick_pattern in candlestick_patterns:
            if candlestick_pattern.match(stock, prices):
                print(f'Pattern {candlestick_pattern.name()} matched')
        print(f'End analysis {code}')
    return None
