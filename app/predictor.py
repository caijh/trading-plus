import numpy as np
import pandas as pd
import plotly.graph_objects as go
from Lib import os
from keras.src.saving import load_model

from data_utils import load_and_preprocess_data, create_dataset
from train_model import train_model, Attention


def predict_future_prices(model, last_sequence, scaler, close_index, features, future_days=20):
    future_predictions = []
    current_seq = last_sequence.copy()
    for _ in range(future_days):
        next_pred_scaled = model.predict(current_seq.reshape(1, current_seq.shape[0], current_seq.shape[1]), verbose=0)
        dummy = np.zeros((1, len(features)))
        dummy[0, close_index] = next_pred_scaled[0][0]
        next_full_scaled = dummy[0]

        # 假设 MA10/RSI/MACD/Volume 沿用最后一个值（保守估计）
        new_step = current_seq[-1].copy()
        new_step[close_index] = next_pred_scaled[0][0]
        current_seq = np.vstack((current_seq[1:], new_step))

        future_price = scaler.inverse_transform(dummy)[0, close_index]
        future_predictions.append(future_price)

    return future_predictions


def predict_and_plot(stock, prices, future_days=7):
    df, scaler, scaled_data, features = load_and_preprocess_data(prices)
    sequence_len = 5
    x, y = create_dataset(scaled_data, features, sequence_len, future_days)
    # 训练集
    factor = 1
    split = int(len(x) * factor)
    x_train, y_train = x[:split], y[:split]
    model_path = f'./app/model/model_{stock["stock_code"]}.keras'
    model = None
    # 模型
    if os.path.exists(model_path):
        print("✅ Model exists. Loading model...")
        model = load_model(model_path, custom_objects={'Attention': Attention})
    else:
        print("🔄 Model not found. Training a new model...")
        model = train_model(stock, x_train, y_train, sequence_len, future_days, x.shape[2])

    # 拆分测试集
    factor = 0.5
    x_test = x[int(len(x) * factor):]
    y_test = y[int(len(x) * factor):]

    predicted = model.predict(x_test)
    dummy_cols = np.zeros((predicted.shape[0], len(features)))
    dummy_cols[:, features.index('close')] = predicted[:, 0]
    predicted_prices = scaler.inverse_transform(dummy_cols)[:, features.index('close')].flatten().tolist()

    dummy_y = np.zeros((y_test.shape[0], len(features)))
    dummy_y[:, features.index('close')] = y_test.flatten()
    real_prices = scaler.inverse_transform(dummy_y)[:, features.index('close')].flatten().tolist()

    last_sequence = x[-1]  # 最后一个序列
    future_prices = predict_future_prices(model, last_sequence, scaler, features.index('close'), features, future_days)
    last_date = df.index[-1]
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=len(future_prices), freq='D')

    # 可视化
    # plt.figure(figsize=(14, 6))
    # plt.plot(df.index[-len(y_test)], real_prices, label='Real Price')
    # plt.plot(df.index[-len(predicted_prices)], predicted_prices, label='Predicted Price')
    # plt.plot(future_dates, future_prices, label='Future Predicted Price', color='green')
    # plt.axvline(last_date, linestyle='--', color='gray', label='Prediction Start')
    # plt.title('Stock Price Prediction')
    # plt.xlabel('Date')
    # plt.ylabel('Price')
    # plt.legend()
    # plt.grid(True)
    # plt.tight_layout()
    # # plt.show()
    # plt.savefig(f"./app/static/P_{stock['stock_code']}.png")

    # 创建图表
    fig = go.Figure(data=go.Candlestick(
        x=df.index,  # 日期和四组数据
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        increasing=dict(line=dict(color='red')),  # 涨：红色
        decreasing=dict(line=dict(color='green'))  # 跌：绿色
    ))

    # 真实价格
    fig.add_trace(go.Scatter(
        x=df.index[-len(real_prices):], y=real_prices,
        mode='lines', name='Real Price', line=dict(color='blue')
    ))

    # 历史预测价格
    fig.add_trace(go.Scatter(
        x=df.index[-len(predicted_prices):], y=predicted_prices,
        mode='lines', name='Predicted Price', line=dict(color='orange')
    ))

    # 未来预测价格
    fig.add_trace(go.Scatter(
        x=future_dates, y=future_prices,
        mode='lines', name='Future Predicted Price', line=dict(color='green')
    ))

    # 预测起始线
    # ✅ 用 scatter 添加一条灰色竖线
    fig.add_trace(go.Scatter(
        x=[last_date, last_date],
        y=[min(min(real_prices), min(predicted_prices), min(future_prices)),
           max(max(real_prices), max(predicted_prices), max(future_prices))],
        mode='lines',
        line=dict(color='gray', dash='dash'),
        name='Prediction Start',
        showlegend=True
    ))

    # 设置图表布局
    fig.update_layout(
        title='Stock Price Prediction',
        xaxis_title='Date',
        yaxis_title='Price',
        legend=dict(x=0, y=1.1, orientation='h'),
        template='plotly_white',
        xaxis=dict(
            type='date',
            rangebreaks=[
                # ⛔ 自动跳过周末
                dict(bounds=["sat", "mon"]),
                # ✅ 可选跳过节假日（如果你有假日列表）
                # dict(values=holiday_dates)
            ]
        ),
    )

    # 保存为HTML交互式文件
    html_path = f"./app/static/predict/{stock['stock_code']}.html"
    fig.write_html(html_path)

    return future_prices
