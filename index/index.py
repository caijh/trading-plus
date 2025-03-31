import requests

from environment.env import env_vars
from stock.stock import analyze_stock, KType


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
    """
    根据指数代码获取指数成分股列表。

    参数:
    code (str): 指数代码。

    返回:
    list: 指数成分股列表，如果请求失败或数据不可用，则返回空列表。
    """
    # 从环境变量中获取交易数据URL
    # 构造获取指数成分股的URL
    url = f'{env_vars.TRADING_DATA_URL}/index/{code}/stocks'

    print(f'从数据源获取指数成分股数据，url: {url}')

    # 发起HTTP GET请求获取数据
    data = requests.get(url).json()

    # 检查返回的数据中是否有错误码
    if data['code'] == 0:
        # 如果没有错误，返回指数成分股数据
        return data['data']
    else:
        # 如果有错误，返回空列表
        return []


def analyze_index():
    """
    分析股票指数

    该函数通过获取股票指数列表，并对每个指数进行分析，以找出具有特定模式的指数。
    它主要关注的是日K线图中的模式。

    Returns:
        list: 包含有效模式的股票指数列表。
    """
    # 获取股票指数列表
    data = get_stock_index_list()
    indexes = []
    for index in data:
        # 分析每个指数的日K线图模式
        stock = analyze_stock(index, k_type=KType.DAY)
        # 如果存在模式，则将该指数添加到有效指数列表中
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
