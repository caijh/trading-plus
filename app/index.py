import requests

from env import env_vars
from stock import KType, analyze_stock


def get_stock_index_list():
    trading_data_url = env_vars.TRADING_DATA_URL
    url = f'{trading_data_url}/index/list'
    print(url)
    data = requests.get(url).json()
    if data['code'] == 0:
        return data['data']
    else:
        return []


def get_index_stocks(code):
    trading_data_url = env_vars.TRADING_DATA_URL
    url = f'{trading_data_url}/index/{code}/stocks'
    data = requests.get(url).json()
    if data['code'] == 0:
        return data['data']
    else:
        return []


def analyze_index():
    data = get_stock_index_list()
    indexes = []
    for index in data:
        stock = analyze_stock(index, k_type=KType.DAY)
        if len(stock['patterns']) > 0:
            indexes.append(index)

    return indexes


def analyze_index_stocks(code):
    data = get_index_stocks(code)
    stocks = []
    for item in data:
        stock = {'code': item['stock_code'], 'name': item['stock_name']}
        analyze_stock(stock, k_type=KType.DAY)
        if len(stock['patterns']) > 0:
            stocks.append(stock)

    return stocks
