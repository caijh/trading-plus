import pandas as pd
import pandas_ta as ta

from indicator.service import volume_registry


class SAR:
    name = 'SAR'

    def __init__(self, signal=1):
        """
        Parabolic SAR 策略

        参数:
        - signal: 1 表示买入信号（SAR 从上转到下），-1 表示卖出信号（SAR 从下转到上）
        """
        self.signal = signal
        self.label = 'SAR'
        self.weight = 1

    def match(self, stock, df):
        if df is None or len(df) < 3:
            print(f'{stock["code"]} 数据不足，无法计算 PSAR')
            return False

        # 计算 SAR（默认加速因子 step=0.02, max_step=0.2）
        psar = ta.psar(df['high'], df['low'], df['close'])
        if 'PSARl_0.02_0.2' not in psar.columns or 'PSARs_0.02_0.2' not in psar.columns:
            print(f'{stock["code"]} PSAR计算失败')
            return False

        # 最新一条 SAR 值
        psar_last = psar['PSARl_0.02_0.2'].iloc[-1] if not pd.isna(psar['PSARl_0.02_0.2'].iloc[-1]) else \
            psar['PSARs_0.02_0.2'].iloc[-1]
        psar_prev = psar['PSARl_0.02_0.2'].iloc[-2] if not pd.isna(psar['PSARl_0.02_0.2'].iloc[-2]) else \
            psar['PSARs_0.02_0.2'].iloc[-2]
        close_last = df['close'].iloc[-1]
        close_prev = df['close'].iloc[-2]

        # 买入信号：SAR 从上转到下（之前 close < SAR，当前 close > SAR）
        if self.signal == 1:
            return close_prev < psar_prev and close_last > psar_last

        # 卖出信号：SAR 从下转到上（之前 close > SAR，当前 close < SAR）
        elif self.signal == -1:
            return close_prev > psar_prev and close_last < psar_last

        return False

    def get_volume_confirm_patterns(self):
        return volume_registry.get(self.name).get(self.signal)
