import numpy as np
import pandas as pd
import ta.momentum as momentum
import ta.trend as trend
import ta.volatility as volatility
from sklearn.preprocessing import StandardScaler
from ta.volume import VolumeWeightedAveragePrice


def load_and_preprocess_data(prices):
    df = pd.DataFrame(prices)
    df['close'] = df['close'].astype(float)
    df['open'] = df['open'].astype(float)
    df['low'] = df['low'].astype(float)
    df['high'] = df['high'].astype(float)
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
    df.sort_values('date', inplace=True)
    df.set_index('date', inplace=True)

    # 添加更多技术指标
    df['MA5'] = df['close'].rolling(5).mean()
    df['MA10'] = df['close'].rolling(10).mean()
    df['MA20'] = df['close'].rolling(20).mean()
    df['RSI14'] = momentum.RSIIndicator(close=df['close'], window=14).rsi()
    df['RSI7'] = momentum.RSIIndicator(close=df['close'], window=7).rsi()
    df['MACD'] = trend.MACD(close=df['close']).macd()
    df['ATR'] = volatility.AverageTrueRange(high=df['high'], low=df['low'], close=df['close'],
                                            window=14).average_true_range()

    price = prices[0]
    if float(price['volume']) > 0:
        df['volume'] = df['volume'].astype(float)
        df['VWAP'] = VolumeWeightedAveragePrice(high=df['high'], low=df['low'], close=df['close'], volume=df['volume'],
                                                window=14).volume_weighted_average_price()
        features = ['open', 'high', 'low', 'close', 'MA5', 'MA10', 'MA20', 'RSI14', 'RSI7', 'MACD', 'ATR', 'VWAP']
    else:
        features = ['open', 'high', 'low', 'close', 'MA5', 'MA10', 'MA20', 'RSI14', 'RSI7', 'MACD', 'ATR']

    # 删除缺失值
    df.dropna(subset=features, inplace=True)

    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(df[features])

    return df, scaler, scaled_data, features


def create_dataset(data, features, sequence_length, future_days):
    x, y = [], []
    for i in range(sequence_length, len(data) - future_days):
        x.append(data[i - sequence_length:i])
        y.append(data[i + future_days, features.index('close')])
    return np.array(x), np.array(y)
