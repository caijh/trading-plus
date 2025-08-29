from indicator.base import Indicator
from indicator.ma_volume_registry import volume_registry


class KDJ(Indicator):
    label = ''
    signal = 1
    weight = 1
    name = 'KDJ'

    def __init__(self, signal=1, recent=1, use_j_filter=True):
        """
        参数:
        - signal: 1表示金叉买入信号，-1表示死叉卖出信号
        - recent: 检查最近几天是否有信号
        - use_j_filter: 是否使用J值过滤极端信号
        """
        self.signal = signal
        self.label = 'KDJ'
        self.recent = recent
        self.use_j_filter = use_j_filter

    def match(self, stock, df, trending, direction):
        if df is None or len(df) < 15:
            return False

        # 计算 KDJ
        kdj_df = df.ta.stoch(high='high', low='low', close='close', k=9, d=3, smooth_d=3)
        kdj_df.rename(columns={'STOCHk_9_3_3': 'K', 'STOCHd_9_3_3': 'D'}, inplace=True)
        kdj_df['J'] = 3 * kdj_df['K'] - 2 * kdj_df['D']

        # 构建信号条件
        if self.signal == 1:
            # 金叉条件
            cond = (kdj_df['K'].shift(1) < kdj_df['D'].shift(1)) & (kdj_df['K'] > kdj_df['D']) & (kdj_df['D'] < 20)
            if self.use_j_filter:
                cond &= kdj_df['J'] < 30  # J 值辅助过滤，可调整阈值
        elif self.signal == -1:
            # 死叉条件
            cond = (kdj_df['K'].shift(1) > kdj_df['D'].shift(1)) & (kdj_df['K'] < kdj_df['D']) & (kdj_df['D'] > 80)
            if self.use_j_filter:
                cond &= kdj_df['J'] > 70  # J 值辅助过滤，可调整阈值
        else:
            return False

        df[f'{self.label}_Signal'] = cond.fillna(False)

        # 最近 N 天是否有信号
        return df[f'{self.label}_Signal'].tail(self.recent).any()


    def get_volume_confirm_patterns(self):
        return volume_registry.get(self.name).get(self.signal)
