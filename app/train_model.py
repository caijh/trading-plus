import tensorflow.python.keras.backend as K
from keras import Sequential, Input, Layer
from keras.src.layers import LSTM, Dense, Dropout, BatchNormalization


class Attention(Layer):
    def __init__(self, **kwargs):
        super(Attention, self).__init__(**kwargs)

    def build(self, input_shape):
        self.W = self.add_weight(name='att_weight', shape=(input_shape[-1], 1),
                                 initializer='normal', trainable=True)
        self.b = self.add_weight(name='att_bias', shape=(input_shape[1], 1),
                                 initializer='zeros', trainable=True)
        super(Attention, self).build(input_shape)

    def call(self, x):
        e = K.tanh(K.dot(x, self.W) + self.b)
        a = K.softmax(e, axis=1)
        output = x * a
        return K.sum(output, axis=1)


def train_model(stock, x, y, time_step, feature_dim):
    model = Sequential()
    model.add(Input(shape=(time_step, feature_dim)))
    model.add(LSTM(64, return_sequences=True))
    model.add(Dropout(0.2))
    model.add(BatchNormalization())
    # model.add(LSTM(64))
    model.add(Dropout(0.2))
    # model.add(Dense(32, activation='relu'))
    model.add(Attention())  # Attention Layer
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mean_squared_error')
    model.fit(x, y, epochs=10000, batch_size=32, validation_split=0.1, verbose=1)
    model.save(f'./app/model/model_{stock["stock_code"]}.keras')

    return model


if __name__ == '__main__':
    train_model()
