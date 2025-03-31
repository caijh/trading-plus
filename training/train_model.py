import tensorflow as tf
from keras import Sequential, Input, Layer
from keras.src.callbacks import EarlyStopping, ReduceLROnPlateau
from keras.src.layers import LSTM, Dense, Dropout, BatchNormalization, Bidirectional


class Attention(Layer):
    """
    Attention层，继承自Layer类，用于在神经网络中实现注意力机制。
    注意力机制可以帮助模型更好地聚焦于输入中的重要部分，尤其是在序列数据处理任务中。
    """

    def __init__(self, **kwargs):
        """
        构造函数，初始化Attention层。
        """
        super(Attention, self).__init__(**kwargs)

    def build(self, input_shape):
        """
        构建Attention层，包括初始化权重和偏置。

        参数:
        - input_shape: 输入数据的形状，用于确定权重矩阵的尺寸。
        """
        # 初始化权重矩阵W和偏置向量b，W用于输入特征的线性变换，b为偏置项。
        self.W = self.add_weight(name='att_weight', shape=(input_shape[-1], 1),
                                 initializer='normal', trainable=True)
        self.b = self.add_weight(name='att_bias', shape=(input_shape[1], 1),
                                 initializer='zeros', trainable=True)
        super(Attention, self).build(input_shape)

    def call(self, x):
        """
        实现Attention层的前向传播，计算带有注意力的输出。

        参数:
        - x: 输入数据，形状为(batch_size, sequence_length, input_dim)。

        返回:
        - output: 注意力机制处理后的输出。
        """
        # 计算注意力分数，使用tanh激活函数。
        e = tf.tanh(tf.matmul(x, self.W) + self.b)
        # 对注意力分数进行softmax，得到注意力权重。
        a = tf.nn.softmax(e, axis=1)
        # 应用注意力权重到输入x上，并求和，得到注意力机制处理后的输出。
        output = x * a
        # 最终输出是注意力输出的总和与最后一个时间步的输入的加权和。
        return tf.reduce_sum(output, axis=1) + x[:, -1, :] * 0.2


def train_model(stock, x, y, sequence_len, future_days, feature_dim):
    model = Sequential()
    model.add(Input(shape=(sequence_len, feature_dim)))
    model.add(Bidirectional(LSTM(512, return_sequences=True)))
    model.add(Dropout(0.3))
    model.add(BatchNormalization())
    model.add(Bidirectional(LSTM(256, return_sequences=True)))
    model.add(Dropout(0.3))
    model.add(Attention())
    model.add(Dense(256, activation='relu'))
    model.add(Dropout(0.3))
    model.add(Dense(1))

    model.compile(optimizer='adam', loss='mean_squared_error')

    callbacks = [
        EarlyStopping(
            monitor='loss',  # 监控验证损失
            patience=50,  # 允许 50 轮没有改善
            min_delta=0.001,  # 最小改善幅度
            mode='min',
            restore_best_weights=True  # 恢复到最佳权重
        ),
        ReduceLROnPlateau(
            monitor='loss',  # 监控验证损失
            factor=0.2,  # 学习率减少因子
            patience=20,  # 允许 20 轮没有改善
            min_lr=0.00001  # 最小学习率
        )
    ]

    model.fit(x, y, epochs=1000, batch_size=128, validation_split=0.0, callbacks=callbacks, verbose=1)
    model.save(f'./training/model/{stock["code"]}.keras')

    return model