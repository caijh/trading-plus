import numpy as np
import pandas as pd


class R2:
    def __init__(self, signal=1, period=20, r2_threshold=0.5, use_log=True):
        """
        R² 决定系数趋势确认指标
        参数:
        - signal: 1 确认做多；-1 确认做空
        - period: 回归窗口长度
        - r2_threshold: R²阈值，越高表示越强的线性趋势（0~1）
        - use_log: 是否对收盘价取对数做回归（更稳健）
        """
        self.signal = signal
        self.period = period
        self.r2_threshold = r2_threshold
        self.use_log = use_log
        self.label = 'R2'
        self.weight = 1

    @staticmethod
    def _r2_and_slope(y: np.ndarray) -> tuple[float, float]:
        """给定窗口y，返回 (R², slope)。x为等距时间索引。"""
        n = y.size
        x = np.arange(n, dtype=float)

        # 处理常数序列
        if np.allclose(y, y[0]) or n < 2:
            return 0.0, 0.0

        sumx = x.sum()
        sumy = y.sum()
        sumx2 = (x * x).sum()
        sumy2 = (y * y).sum()
        sumxy = (x * y).sum()

        # 斜率（最小二乘）
        denom = (n * sumx2 - sumx * sumx)
        if denom == 0:
            slope = 0.0
        else:
            slope = (n * sumxy - sumx * sumy) / denom

        # 相关系数 r，再平方得 R²
        num = (n * sumxy - sumx * sumy)
        denom_r = np.sqrt((n * sumx2 - sumx * sumx) * (n * sumy2 - sumy * sumy))
        if denom_r == 0:
            r2 = 0.0
        else:
            r = num / denom_r
            r2 = float(r * r)
        return r2, float(slope)

    def match(self, stock, prices, df):
        """
        作为“确认指标（OR逻辑的一员）”：
        - 多头确认：R² >= 阈值 且 斜率 > 0
        - 空头确认：R² >= 阈值 且 斜率 < 0
        """
        if df is None or len(df) < self.period:
            print(f'{stock.get("code", "")} 数据不足，无法计算 R² 指标')
            return False

        close = df['close'].values
        window = close[-self.period:]
        if self.use_log:
            # 防止非正值导致对数报错
            if np.any(window <= 0):
                # 回退到原始价格
                y = window
            else:
                y = np.log(window)
        else:
            y = window

        r2, slope = self._r2_and_slope(y)

        if self.signal == 1:
            return (r2 >= self.r2_threshold) and (slope > 0)
        elif self.signal == -1:
            return (r2 >= self.r2_threshold) and (slope < 0)
        return False

    def rolling_series(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        可选：生成整段时间的滚动 R² 与 slope 序列，便于调参与可视化。
        返回包含两列：f'{self.label}_r2', f'{self.label}_slope'
        """
        s = df['close'].astype(float)
        if self.use_log:
            s = s.where(s > 0).apply(lambda v: np.log(v) if pd.notna(v) else v)

        def _calc(arr):
            r2, slope = self._r2_and_slope(np.asarray(arr, dtype=float))
            # rolling.apply 只能返回标量，这里拼成浮点组合再拆分不方便；
            # 采用两次rolling分别计算更直观，故此函数仅作占位。
            return r2

        # R²序列
        r2_series = s.rolling(self.period, min_periods=self.period).apply(
            lambda arr: self._r2_and_slope(np.asarray(arr, dtype=float))[0],
            raw=True
        )
        # slope序列
        slope_series = s.rolling(self.period, min_periods=self.period).apply(
            lambda arr: self._r2_and_slope(np.asarray(arr, dtype=float))[1],
            raw=True
        )

        out = pd.DataFrame({
            f'{self.label}_r2': r2_series,
            f'{self.label}_slope': slope_series
        }, index=df.index)
        return out
