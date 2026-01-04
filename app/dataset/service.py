import pandas as pd

from app.calculate.service import detect_turning_point_indexes
from app.stock.service import get_adj_factor


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
    if stock['stock_type'] == 'Index':
        df = df[(df['close'] > 0)]
    else:
        df = df[(df['close'] > 0) & (df['volume'] > 0)]

    # 将日期格式从字符串转换为datetime对象
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
    # 根据日期对DataFrame进行排序
    df.sort_values('date', inplace=True)
    # 复权价处理
    df = apply_forward_adjustment_all_prices(stock, df)

    # 计算移动平均线和指数移动平均线，并保留三位小数
    df['EMA5'] = df['close'].ewm(span=5, adjust=False).mean().round(3)
    df['SMA5'] = df['close'].rolling(window=5).mean().round(3)
    df['SMA10'] = df['close'].rolling(window=10).mean().round(3)
    df['SMA20'] = df['close'].rolling(window=20).mean().round(3)
    df['SMA50'] = df['close'].rolling(window=50).mean().round(3)
    df['SMA120'] = df['close'].rolling(window=120).mean().round(3)
    df['SMA200'] = df['close'].rolling(window=200).mean().round(3)

    # 找出均线的拐点位置
    turning_points_idxes, turning_up_idxes, turning_down_idxes = detect_turning_point_indexes(df['EMA5'], df)
    turning_up_idxes = [idx for idx in turning_up_idxes if idx < df.shape[0]]
    turning_down_idxes = [idx for idx in turning_down_idxes if idx < df.shape[0]]
    # 向上拐点turning_up_idxes, df['turning']=1, 向下拐点turning_down_idxes, df['turning']=-1,其他df['turning']=0
    # 新增 turning 列，默认值为 0
    df['turning'] = 0
    turning_col_idx = df.columns.get_loc('turning')

    # 标记向上拐点为 1
    df.iloc[turning_up_idxes, turning_col_idx] = 1

    # 标记向下拐点为 -1
    df.iloc[turning_down_idxes, turning_col_idx] = -1

    # 设置日期列为DataFrame的索引
    df.set_index('date', inplace=True)

    return df


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
    min_loc = adj_df.index.min()
    max_loc = adj_df.index.max()
    start_date = adj_df.iloc[min_loc]['date'].strftime("%Y-%m-%d")
    end_date = adj_df.iloc[max_loc]['date'].strftime("%Y-%m-%d")

    factor_df = get_adj_factor(stock, start_date, end_date)
    adj_df = adj_df.merge(factor_df, on='date', how='left')
    adj_df = adj_df.dropna(subset=['close', 'adj_factor'])
    n_digits = 3 if stock['stock_type'] == 'Fund' else 2
    for col in ['open', 'high', 'low', 'close']:
        adj_df[f'{col}'] = (adj_df[col].astype(float) * adj_df['adj_factor'].astype(float)).round(n_digits)

    return adj_df
