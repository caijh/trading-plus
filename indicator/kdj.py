from indicator.service import volume_registry


class KDJ:
    label = ''
    signal = 1
    weight = 1
    name = 'KDJ'

    def __init__(self, signal, recent=1):
        self.signal = signal
        self.label = 'KDJ'
        self.recent = recent

    def match(self, stock, df):
        if df is None or len(df) < 15:
            return False

        # 计算 KDJ 指标
        kdj_df = df.ta.stoch(high='high', low='low', close='close', k=9, d=3, smooth_d=3)

        # 重命名列
        kdj_df.rename(columns={'STOCHk_9_3_3': 'K', 'STOCHd_9_3_3': 'D'}, inplace=True)
        kdj_df['J'] = 3 * kdj_df['K'] - 2 * kdj_df['D']

        if self.signal == 1:
            # 识别 KDJ 金叉（K 上穿 D，且 D < 20）
            df[f'{self.label}_Signal'] = (kdj_df['K'].shift(1) < kdj_df['D'].shift(1)) & (kdj_df['K'] > kdj_df['D']) & (
                kdj_df['D'] < 20) & (kdj_df['J'] < 20)
        elif self.signal == -1:
            # 识别 KDJ 死叉（K 下穿 D，且 D > 80）
            df[f'{self.label}_Signal'] = (kdj_df['K'].shift(1) > kdj_df['D'].shift(1)) & (kdj_df['K'] < kdj_df['D']) & (
                kdj_df['D'] > 80) & (kdj_df['J'] > 80)
        else:
            raise False

        # 取最近几天数据
        recent_signals = df.tail(self.recent)

        # 判断是否有交易信号
        kdj_signal = recent_signals[f'{self.label}_Signal'].any()

        return kdj_signal

    def get_volume_confirm_patterns(self):
        return volume_registry.get(self.name).get(self.signal)
