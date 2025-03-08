import requests

from env import env_vars
from stock import get_stock_price


def get_stock_index_list():
    trading_data_url = env_vars.TRADING_DATA_URL
    url = f'{trading_data_url}/index/list'
    print(url)
    data = requests.get(url).json()
    if data['code'] == 0:
        return data['data']
    else:
        return []


def do_analysis_index():
    data = get_stock_index_list()
    for index in data:
        print(f'Start analysis {index}')
        prices = get_stock_price(index['code'])
        if not prices:
            continue
        else:
            print(f'End analysis {index}')

    return None
