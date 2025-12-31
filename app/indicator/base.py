import pandas as pd


class Indicator:

    def match(self, stock, df, trending, direction):
        return False

    @staticmethod
    def trend_confirmation(series: pd.Series, trend):
        """
        判断 PVI 的趋势确认信号
        """
        # PVI 上升，表明在放量情况下股价上涨，是牛市信号
        latest = series.iloc[-1]
        prev = series.iloc[-2]
        if trend == "bullish":
            return latest > prev
        elif trend == "bearish":
            return latest < prev

        return False

    @staticmethod
    def divergence(series: pd.Series, divergence):
        """
        判断 PVI 的背离信号
        """
        # PVI 下降，表明在放量情况下股价下跌，是熊市信号
        latest = series.iloc[-1]
        prev = series.iloc[-2]
        if divergence == 'bullish':
            # 底背离：价格下跌但 PVI 上涨，暗示买盘力量增强
            return latest > prev
        elif divergence == 'bearish':
            # 顶背离：价格上涨但 PVI 下跌，暗示卖盘力量增强
            return latest < prev

        return False
