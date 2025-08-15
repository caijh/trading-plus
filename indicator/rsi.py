import pandas_ta as ta

from indicator.service import volume_registry


class RSI:
    weight = 1
    signal = 1
    recent = 1
    name = 'RSI'

    def __init__(self, signal, recent=3):
        self.signal = signal
        self.label = 'RSI'
        self.recent = recent

    def match(self, stock, df):
        # 计算 RSI 指标
        rsi_df = ta.rsi(df['close'], length=14, signal_indicators=True)  # type: ignore
        # 重命名列
        rsi_df.rename(columns={'RSI_14': 'RSI'}, inplace=True)  # type: ignore
        df[f'{self.label}'] = rsi_df['RSI']
        if self.signal == 1:
            # 识别 RSI 低于 30 且反弹（买入信号）
            df[f'{self.label}_Signal'] = (rsi_df['RSI'].shift(1) < 30) & (rsi_df['RSI'] > rsi_df['RSI'].shift(1))
        elif self.signal == -1:
            # 识别 RSI 高于 70 且下跌（卖出信号）
            df[f'{self.label}_Signal'] = (rsi_df['RSI'].shift(1) > 70) & (rsi_df['RSI'] < rsi_df['RSI'].shift(1))
        else:
            return False

        recent_signals = df.tail(self.recent)

        # 判断是否有交易信号
        rsi_signal = recent_signals[f'{self.label}_Signal'].any()

        return rsi_signal

    def get_volume_confirm_patterns(self):
        return volume_registry.get(self.name).get(self.signal)
