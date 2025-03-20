from keras import Sequential, Input
from keras.src.layers import LSTM, Dense, Dropout, BatchNormalization


def train_model(stock, x, y, time_step):
    model = Sequential()
    model.add(Input(shape=(time_step, 1)))
    model.add(LSTM(64, return_sequences=True))
    model.add(Dropout(0.2))
    model.add(BatchNormalization())
    model.add(LSTM(64))
    model.add(Dropout(0.2))
    # model.add(Dense(32, activation='relu'))
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mean_squared_error')
    model.fit(x, y, epochs=10000, batch_size=32, verbose=0)
    model.save(f'./app/model/model_{stock["stock_code"]}.keras')

    return model


if __name__ == '__main__':
    train_model()
