import numpy as np
import pandas as pd

from data_utils import load_and_preprocess_data, create_dataset
from train_model import train_model


# import matplotlib.pyplot as plt
# from datetime import timedelta
# from keras.src.saving import load_model


def predict_future_prices(model, data, scaler, future_days=7, sequence_length=60):
    """
    data: 原始归一化后的数据（如：最近60天的归一化价格）
    model: 已训练好的模型
    scaler: 用于反归一化结果
    future_days: 想预测几天
    sequence_length: 每次模型输入的时间步长度，通常60

    返回：未来7天的预测价格（已经反归一化）
    """
    future_predictions = []

    # 创建初始输入序列（最近60天）
    input_sequence = data[-sequence_length:].reshape(1, sequence_length, 1)

    for _ in range(future_days):
        # 模型预测下一个价格
        next_price = model.predict(input_sequence, verbose=0)

        # 保存预测值（还未反归一化）
        future_predictions.append(next_price[0][0])

        # 更新输入序列：去掉最早一天，加入最新预测
        input_sequence = np.append(input_sequence[:, 1:, :], [[[next_price[0][0]]]], axis=1)

    # 反归一化所有预测值
    future_predictions = np.array(future_predictions).reshape(-1, 1)
    future_prices = scaler.inverse_transform(future_predictions)

    return future_prices


def predict_and_plot(stock, prices, future_days=7):
    df, scaler, scaled_data = load_and_preprocess_data(prices)
    time_step = 5
    x, y = create_dataset(scaled_data, time_step)
    x = x.reshape(x.shape[0], x.shape[1], 1)
    # 训练集
    factor = 1
    split = int(len(x) * factor)
    x_train, y_train = x[:split], y[:split]

    # 模型
    model = train_model(x_train, y_train, time_step)

    # 拆分测试集
    x_test = x[int(len(x) * factor):]
    y_test = y[int(len(x) * factor):]

    predicted = model.predict(x_train)
    predicted_prices = scaler.inverse_transform(predicted)
    real_prices = scaler.inverse_transform(y_train.reshape(-1, 1))

    future_prices = predict_future_prices(model, scaled_data, scaler, future_days=future_days)
    last_date = df.index[-1]
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=len(future_prices), freq='D')

    # 可视化
    # plt.figure(figsize=(14, 6))
    # plt.plot(df.index[-len(y_train):], real_prices, label='Real Price')
    # plt.plot(df.index[-len(predicted_prices):], predicted_prices, label='Predicted Price')
    # plt.plot(future_dates, future_prices, label='Future Predicted Price', color='green')
    # plt.axvline(last_date, linestyle='--', color='gray', label='Prediction Start')
    # plt.title('Stock Price Prediction')
    # plt.xlabel('Date')
    # plt.ylabel('Price')
    # plt.legend()
    # plt.grid(True)
    # plt.tight_layout()
    # plt.show()
    # plt.savefig(f"./app/static/P_{stock['stock_code']}.png")

    return future_prices


if __name__ == '__main__':
    predict_and_plot()
