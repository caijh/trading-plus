import pandas_ta as ta

from indicator.base import Indicator
from indicator.ma_volume_registry import volume_registry


class SAR(Indicator):
    name = 'SAR'

    def __init__(self, signal=1, step=0.02, max_step=0.2):
        """
        Parabolic SAR 策略

        参数:
        - signal: 1 表示买入信号，-1 表示卖出信号
        - step: 加速因子，默认为 0.02
        - max_step: 最大加速因子，默认为 0.2
        """
        self.signal = signal
        self.step = step
        self.max_step = max_step
        self.label = 'SAR'
        self.weight = 1

    def match(self, stock, df, trending, direction):
        if df is None or len(df) < 3:
            print(f'{stock["code"]} 数据不足，无法计算 PSAR')
            return False

        # 动态生成 PSAR 列名
        psar_columns = [f'PSARl_{self.step}_{self.max_step}', f'PSARs_{self.step}_{self.max_step}']

        # 计算 PSAR
        psar = ta.psar(df['high'], df['low'], df['close'], af0=self.step, af=self.step, max_af=self.max_step)

        # 检查 PSAR 计算结果是否有效
        if not all(col in psar.columns for col in psar_columns):
            print(f'{stock["code"]} PSAR计算失败，请检查参数或数据')
            return False

        # 合并多余的列，只保留 SAR 点位和收盘价
        psar['psar'] = psar[psar_columns[0]].fillna(psar[psar_columns[1]])
        df['psar'] = psar['psar']

        # 向量化处理，判断趋势反转
        # 通过 shift(-1) 比较前一根K线，以判断趋势变化
        df['sar_is_below'] = df['psar'] < df['close']
        df['prev_sar_is_below'] = df['sar_is_below'].shift(1)

        # 买入信号: SAR 从上转下 (前一根K线 SAR 在价格上方，当前在下方)
        if self.signal == 1:
            # 最后一个点的趋势反转
            return df['prev_sar_is_below'].iloc[-1] == False and df['sar_is_below'].iloc[-1] == True

        # 卖出信号: SAR 从下转上 (前一根K线 SAR 在价格下方，当前在上方)
        elif self.signal == -1:
            # 最后一个点的趋势反转
            return df['prev_sar_is_below'].iloc[-1] == True and df['sar_is_below'].iloc[-1] == False

        return False

    def get_volume_confirm_patterns(self):
        return volume_registry.get(self.name).get(self.signal)