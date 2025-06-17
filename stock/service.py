import json
from enum import Enum
from io import StringIO

import akshare as ak
import pandas as pd

from environment.service import env_vars
from extensions import redis_client
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
    value = redis_client.get(f'Trading-Plus:Stock:{code}')
    if value is not None:
        return json.loads(value)

    url = f'{env_vars.TRADING_DATA_URL}/stock?code={code}'
    stock = http_get_with_retries(url, 3, None)
    if stock is not None:
        redis_client.set(f'Trading-Plus:Stock:{code}', json.dumps(stock), 30)
    return stock


def get_stock_prices(code, k_type=KType.DAY):
    """
    根据股票代码和K线类型获取股票价格数据。

    参数:
    code (str): 股票代码，用于标识特定的股票。
    k_type (KType): K线类型，默认为日K线。这决定了返回的价格数据的时间周期。

    返回:
    list: 如果请求成功，返回包含股票价格数据的列表；如果请求失败或不支持的k_type，则返回空列表。
    """
    # 当请求的是日K线数据时，构造请求URL并发送请求

    prices = redis_client.get(f'Trading-Plus:Stock:{code}:{k_type}')
    if prices is not None:
        return json.loads(prices)

    if k_type == KType.DAY:
        url = f'{env_vars.TRADING_DATA_URL}/stock/price/daily?code={code}'

        if env_vars.DEBUG:
            print(f'Get stock price from {url} , code = {code}, k_type = {k_type}')

        prices = http_get_with_retries(url, 3, [])

        if len(prices) > 0:
            redis_client.set(f'Trading-Plus:Stock:{code}:{k_type}', json.dumps(prices), 90)

        return prices
    # 如果k_type不是DAY，直接返回空列表，表示不支持的k_type
    return []


def get_stock_price(code):
    url = f'{env_vars.TRADING_DATA_URL}/stock/price?code={code}'
    return http_get_with_retries(url, 3, None)


def get_adj_factor(stock, start_date: str, end_date: str):
    exchange = stock['exchange']
    if exchange == 'SSE':
        return get_adj_factor_from_akshare(f"sh{stock['stock_code']}", start_date, end_date)
    elif exchange == 'SZSE':
        return get_adj_factor_from_akshare(f"sz{stock['stock_code']}", start_date, end_date)
    else:
        raise RuntimeError(f"不支持的股票交易所：{exchange}")


def ak_stock_zh_a_daily(symbol: str, start_date: str, end_date: str, adjust=""):
    daily = redis_client.get(f'Trading-Plus:Stock:{symbol}:{start_date}:{end_date}:{adjust}')
    if daily is not None:
        return pd.read_json(StringIO(daily.decode('utf-8')))

    daily = ak.stock_zh_a_daily(symbol=symbol, start_date=start_date, end_date=end_date, adjust=adjust)
    if daily is not None:
        redis_client.set(f'Trading-Plus:Stock:{symbol}:{start_date}:{end_date}:{adjust}', daily.to_json(), 60 * 60)
    return daily

def get_adj_factor_from_akshare(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    通过 AkShare 获取某只 A 股的复权因子（基于收盘价的前复权计算）

    参数:
    - symbol: 股票代码，如 'sh600519' 或 'sz000001'

    返回:
    - DataFrame，包含 ['date', 'close_raw', 'close_qfq', 'adj_factor']
    """
    # 获取原始（不复权）价格
    try:
        df_raw = ak_stock_zh_a_daily(symbol=symbol, start_date=start_date, end_date=end_date, adjust="")  # 不复权
        df_raw = df_raw.reset_index().rename(columns={"date": "date", "close": "close_raw"})
    except Exception as e:
        raise RuntimeError(f"获取原始股价失败：{e}")

    # 获取前复权价格
    try:
        df_qfq = ak_stock_zh_a_daily(symbol=symbol, start_date=start_date, end_date=end_date, adjust="qfq")  # 前复权
        df_qfq = df_qfq.reset_index().rename(columns={"date": "date", "close": "close_qfq"})
    except Exception as e:
        raise RuntimeError(f"获取前复权股价失败：{e}")

    # 合并数据
    df = pd.merge(df_raw[['date', 'close_raw']], df_qfq[['date', 'close_qfq']], on="date", how="inner")

    # 计算复权因子
    df['adj_factor'] = df['close_qfq'] / df['close_raw']
    # 将日期格式从字符串转换为datetime对象
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
    return df[['date', 'adj_factor']]
