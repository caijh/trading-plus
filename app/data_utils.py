import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler


def load_and_preprocess_data(prices):
    df = pd.DataFrame(prices)
    df['close'] = df['close'].astype(float)
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
    df.sort_values('date', inplace=True)
    df.set_index('date', inplace=True)

    df.dropna(subset=['close'], inplace=True)
    close_prices = df['close'].values.reshape(-1, 1)
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(close_prices)

    return df, scaler, scaled_data


def create_dataset(data, sequence_length=60):
    X, y = [], []
    for i in range(sequence_length, len(data)):
        X.append(data[i - sequence_length:i, 0])
        y.append(data[i, 0])
    return np.array(X), np.array(y)
