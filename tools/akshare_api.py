import akshare as ak
import pandas as pd


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
        df_raw = ak.stock_zh_a_daily(symbol=symbol, start_date=start_date, end_date=end_date, adjust="")  # 不复权
        df_raw = df_raw.reset_index().rename(columns={"date": "date", "close": "close_raw"})
    except Exception as e:
        raise RuntimeError(f"获取原始股价失败：{e}")

    # 获取前复权价格
    try:
        df_qfq = ak.stock_zh_a_daily(symbol=symbol, start_date=start_date, end_date=end_date, adjust="qfq")  # 前复权
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


def get_adj_factor(stock, start_date: str, end_date: str):
    exchange = stock['exchange']
    if exchange == 'SSE':
        return get_adj_factor_from_akshare(f"sh{stock['stock_code']}", start_date, end_date)
    elif exchange == 'SZSE':
        return get_adj_factor_from_akshare(f"sz{stock['stock_code']}", start_date, end_date)
    else:
        raise RuntimeError(f"不支持的股票交易所：{exchange}")
