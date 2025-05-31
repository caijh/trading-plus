from enum import Enum

from environment.service import env_vars
from request.service import http_get_with_retries


class KType(Enum):
    DAY = 'D'


def get_stock(code):
    """
    根据股票代码获取股票信息。

    通过发送HTTP GET请求到TRADING_DATA_URL获取股票数据，如果请求成功，
    则解析并返回股票信息，否则返回None。

    参数:
    code (str): 股票代码，用于唯一标识一个股票。

    返回:
    stock: 如果请求成功且数据有效，则返回股票信息，否则返回None。
    """
    # 构造请求URL，包含股票代码
    url = f'{env_vars.TRADING_DATA_URL}/stock?code={code}'
    print(url)
    return http_get_with_retries(url, 3, None)


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
        return http_get_with_retries(url, 3, [])
    # 如果k_type不是DAY，直接返回空列表，表示不支持的k_type
    return []


