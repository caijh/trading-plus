import requests

from env import env_vars
from stock import KType, analyze_stock


def get_stock_index_list():
    """
    获取股票指数列表。

    本函数从预设的交易数据URL中获取股票指数列表数据。URL由环境变量TRADING_DATA_URL指定。

    Returns:
        list: 股票指数列表，如果请求失败或数据源返回错误，返回空列表。
    """
    # 构造请求URL
    url = f'{env_vars.TRADING_DATA_URL}/index/list'
    print(f'从数据源获指示列表数据，url: {url}')
    # 发起GET请求，获取数据，并将响应内容解析为JSON格式
    data = requests.get(url).json()
    # 检查返回的数据中状态码是否为0，表示请求成功
    if data['code'] == 0:
        # 如果请求成功，返回数据中的股票指数列表
        return data['data']
    else:
        # 如果请求失败，返回空列表
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
