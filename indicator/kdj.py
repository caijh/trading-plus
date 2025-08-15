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

        # 计算 KDJ
        kdj_df = df.ta.stoch(
            high='high', low='low', close='close',
            k=9, d=3, smooth_d=3
        )
        kdj_df.rename(
            columns={'STOCHk_9_3_3': 'K', 'STOCHd_9_3_3': 'D'},
            inplace=True
        )
        kdj_df['J'] = 3 * kdj_df['K'] - 2 * kdj_df['D']

        # 金叉信号
        if self.signal == 1:
            df[f'{self.label}_Signal'] = (
                (kdj_df['K'].shift(1) < kdj_df['D'].shift(1)) &
                (kdj_df['K'] > kdj_df['D']) &
                (kdj_df['D'] < 20)
            ).fillna(False)
        # 死叉信号
        elif self.signal == -1:
            df[f'{self.label}_Signal'] = (
                (kdj_df['K'].shift(1) > kdj_df['D'].shift(1)) &
                (kdj_df['K'] < kdj_df['D']) &
                (kdj_df['D'] > 80)
            ).fillna(False)
        else:
            return False

        # 最近 N 天是否有信号
        return df[f'{self.label}_Signal'].tail(self.recent).any()


    def get_volume_confirm_patterns(self):
        return volume_registry.get(self.name).get(self.signal)
