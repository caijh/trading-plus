import tensorflow as tf
from keras import Sequential, Input, Layer
from keras.src.callbacks import EarlyStopping, ReduceLROnPlateau
from keras.src.layers import LSTM, Dense, Dropout, BatchNormalization, Bidirectional


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
        e = tf.tanh(tf.matmul(x, self.W) + self.b)
        a = tf.nn.softmax(e, axis=1)
        output = x * a
        return tf.reduce_sum(output, axis=1)


def train_model(stock, x, y, sequence_len, future_days, feature_dim):
    model = Sequential()
    model.add(Input(shape=(sequence_len, feature_dim)))
    model.add(Bidirectional(LSTM(256, return_sequences=True)))
    model.add(Dropout(0.2))
    model.add(BatchNormalization())
    model.add(Bidirectional(LSTM(128, return_sequences=True)))
    model.add(Dropout(0.2))
    model.add(Attention())
    model.add(Dense(128, activation='relu'))
    model.add(Dropout(0.2))
    model.add(Dense(1))

    model.compile(optimizer='adam', loss='mean_squared_error')

    callbacks = [
        EarlyStopping(
            monitor='val_accuracy',  # 监控验证损失
            patience=50,  # 允许 50 轮没有改善
            min_delta=0.001,  # 最小改善幅度
            mode='max',
            restore_best_weights=True  # 恢复到最佳权重
        ),
        ReduceLROnPlateau(
            monitor='val_loss',  # 监控验证损失
            factor=0.2,  # 学习率减少因子
            patience=20,  # 允许 20 轮没有改善
            min_lr=0.00001  # 最小学习率
        )
    ]

    model.fit(x, y, epochs=10000, batch_size=64, validation_split=0.2, callbacks=callbacks, verbose=1)
    model.save(f'./app/model/{stock["stock_code"]}.keras')

    return model