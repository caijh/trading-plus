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


def do_analysis_index():
    data = get_stock_index_list()
    for index in data:
        analyze_stock(index, k_type=KType.DAY)

    return None
