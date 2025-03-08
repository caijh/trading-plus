from enum import Enum

import requests

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
