import numpy as np
import pandas as pd
import ta.momentum as momentum
import ta.trend as trend
from sklearn.preprocessing import MinMaxScaler


def load_and_preprocess_data(prices):
    df = pd.DataFrame(prices)
    df['close'] = df['close'].astype(float)
    df['open'] = df['open'].astype(float)
    df['low'] = df['low'].astype(float)
    df['high'] = df['high'].astype(float)
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
    df.sort_values('date', inplace=True)
    df.set_index('date', inplace=True)

    df['MA10'] = df['close'].rolling(10).mean()
    df['RSI14'] = momentum.RSIIndicator(close=df['close'], window=14).rsi()
    df['RSI7'] = momentum.RSIIndicator(close=df['close'], window=7).rsi()
    df['MACD'] = trend.MACD(close=df['close']).macd()
    df.dropna(subset=['open', 'high', 'low', 'close', 'MA10', 'RSI14', 'RSI7', 'MACD'], inplace=True)
    features = ['open', 'high', 'low', 'close', 'MA10', 'RSI14', 'RSI7', 'MACD']
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(df[features])

    return df, scaler, scaled_data, features


def create_dataset(data, features, sequence_length=60):
    X, y = [], []
    for i in range(sequence_length, len(data)):
        X.append(data[i - sequence_length:i])
        y.append(data[i, features.index('close')])
    return np.array(X), np.array(y)
