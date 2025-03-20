import numpy as np
import pandas as pd
import plotly.graph_objects as go
from Lib import os
from keras.src.saving import load_model

from data_utils import load_and_preprocess_data, create_dataset
from train_model import train_model


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
    model_path = f'./app/model/model_{stock["stock_code"]}.keras'
    model = None
    # 模型
    if os.path.exists(model_path):
        print("✅ Model exists. Loading model...")
        model = load_model(model_path)
    else:
        print("🔄 Model not found. Training a new model...")
        model = train_model(stock, x_train, y_train, time_step)

    # 拆分测试集
    factor = 0.5
    x_test = x[int(len(x) * factor):]
    y_test = y[int(len(x) * factor):]

    predicted = model.predict(x_test)
    predicted_prices = scaler.inverse_transform(predicted).flatten().tolist()
    real_prices = scaler.inverse_transform(y_test.reshape(-1, 1)).flatten().tolist()

    future_prices = predict_future_prices(model, scaled_data, scaler, future_days,
                                          sequence_length=time_step).flatten().tolist()
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
    )
    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "sun"])])

    # 保存为HTML交互式文件
    html_path = f"./app/static/predict/{stock['stock_code']}.html"
    fig.write_html(html_path)

    return future_prices

