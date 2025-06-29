import pandas as pd

from stock.service import get_adj_factor


def create_dataframe(stock, prices):
    """
    创建并返回一个格式化后的DataFrame对象。

    本函数从传入的prices数据中构建一个DataFrame对象，并对数据进行一系列的格式化操作，
    包括数据类型转换、日期格式转换、以及DataFrame的排序和索引设置。

    参数:
    prices : list or dict
        包含股票价格信息的列表或字典。

    返回:
    df : DataFrame
        格式化后，包含股票价格信息的DataFrame对象。
    """
    # 初始化DataFrame对象
    df = pd.DataFrame(prices)

    # 将价格和成交量数据类型转换为float
    df['close'] = df['close'].astype(float)
    df['open'] = df['open'].astype(float)
    df['low'] = df['low'].astype(float)
    df['high'] = df['high'].astype(float)
    df['volume'] = df['volume'].astype(float)

    # 过滤掉close为0的数据
    df = df[df['close'] > 0]

    # 将日期格式从字符串转换为datetime对象
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')

    # 根据日期对DataFrame进行排序
    df.sort_values('date', inplace=True)

    # 设置日期列为DataFrame的索引
    df.set_index('date', inplace=True)

    # 返回格式化后的DataFrame对象
    return apply_forward_adjustment_all_prices(stock, df)


def apply_forward_adjustment_all_prices(stock, df):
    """
    将不复权的开高低收全部转换为前复权价格。
    """
    exchange = stock['exchange']
    if exchange not in ['SSE', 'SZSE']:
        return df

    if stock["stock_type"] == 'Index' or stock["stock_type"] == 'Fund':
        return df

    adj_df = df.copy()

    start_date = adj_df.index.min().strftime("%Y-%m-%d")
    end_date = adj_df.index.max().strftime("%Y-%m-%d")

    factor_df = get_adj_factor(stock, start_date, end_date)

    adj_df = adj_df.merge(factor_df, on='date', how='left')
    adj_df = adj_df.dropna(subset=['close', 'adj_factor'])
    adj_df.sort_values('date', inplace=True)
    adj_df.set_index('date', inplace=True)
    n_digits = 3 if stock['stock_type'] == 'Fund' else 2
    for col in ['open', 'high', 'low', 'close']:
        adj_df[f'{col}'] = (adj_df[col].astype(float) * adj_df['adj_factor'].astype(float)).round(n_digits)

    return adj_df
