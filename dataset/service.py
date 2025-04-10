import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


def create_dataframe(prices):
    df = pd.DataFrame(prices)
    df['close'] = df['close'].astype(float)
    df['open'] = df['open'].astype(float)
    df['low'] = df['low'].astype(float)
    df['high'] = df['high'].astype(float)
    df['volume'] = df['volume'].astype(float)
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
    df.sort_values('date', inplace=True)
    df.set_index('date', inplace=True)
    return df


def load_and_preprocess_data(prices):
    df = create_dataframe(prices)

    # 添加更多技术指标
    df['MA5'] = df['close'].rolling(5).mean()
    # df['MA10'] = df['close'].rolling(10).mean()
    # df['MA20'] = df['close'].rolling(20).mean()
    # df['RSI14'] = momentum.RSIIndicator(close=df['close'], window=14).rsi()
    # df['RSI7'] = momentum.RSIIndicator(close=df['close'], window=7).rsi()
    # df['MACD'] = trend.MACD(close=df['close']).macd()
    # df['ATR'] = volatility.AverageTrueRange(high=df['high'], low=df['low'], close=df['close'],
    #                                         window=14).average_true_range()
    # df['Bollinger_Up'] = volatility.BollingerBands(close=df['close'], window=20, window_dev=2).bollinger_hband()
    # df['Bollinger_Down'] = volatility.BollingerBands(close=df['close'], window=20, window_dev=2).bollinger_lband()
    # price = prices[0]
    # if float(price['volume']) > 0:
    #     df['volume'] = df['volume'].astype(float)
    #     df['VWAP'] = VolumeWeightedAveragePrice(high=df['high'], low=df['low'], close=df['close'], volume=df['volume'],
    #                                             window=14).volume_weighted_average_price()
    #     features = ['open', 'high', 'low', 'close', 'MA5', 'MA10', 'MA20', 'RSI14', 'RSI7', 'MACD', 'ATR', 'VWAP', 'Bollinger_Up', 'Bollinger_Down']
    # else:
    #     features = ['open', 'high', 'low', 'close', 'MA5', 'MA10', 'MA20', 'RSI14', 'RSI7', 'MACD', 'ATR', 'Bollinger_Up', 'Bollinger_Down']

    features = ['close', 'MA5']
    # 删除缺失值
    df.dropna(subset=features, inplace=True)

    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(df[features])

    return df, scaler, scaled_data, features


def create_dataset(data, features, sequence_length, future_days):
    """
    根据给定的数据和特征创建数据集。

    该函数的目的是为了准备机器学习模型的训练数据。它会根据指定的序列长度和未来天数，
    从原始数据中提取输入序列（x）和目标值（y）。

    参数:
    data: 原始数据集，包含了所有需要的特征。
    features: 一个列表，包含了所有需要考虑的特征名称。
    sequence_length: 输入序列的长度，即模型在预测时需要考虑的天数。
    future_days: 预测未来天数的股票价格。

    返回:
    x: 输入序列的数据集，包含了每个时间点前 sequence_length 天的数据。
    y: 目标值的数据集，即每个时间点后 future_days 天的股票收盘价。
    """
    # 初始化 x 和 y 列表
    x, y = [], []

    # 遍历数据集，创建输入序列和目标值
    for i in range(sequence_length, len(data) - future_days):
        # 将序列长度的数据添加到 x 中
        x.append(data[i - sequence_length:i])
        # 将未来天数的股票收盘价添加到 y 中
        y.append(data[i + future_days, features.index('close')])

    # 将 x 和 y 转换为 numpy 数组并返回
    return np.array(x), np.array(y)
