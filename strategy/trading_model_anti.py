import pandas_ta as ta

from strategy.model import TradingStrategy
from strategy.trading_model import TradingModel


class AntiTradingModel(TradingModel):
    def __init__(self):
        super().__init__('AntiTradingModel')

    def get_trading_signal(self, stock, df, trending, direction):
        """
        优化后的 ANTI 策略：结合 KD 指标、均线和成交量。
        """

        # 1. 数据充足性检查 (Added)
        # 至少需要足够的均线计算周期，例如20周期，这里取更长确保数据完整
        if len(df) < 50:
            return 0

        # 2. 计算 KD 指标
        kdj_df = df.ta.stoch(
            high='high',
            low='low',
            close='close',
            k=7,
            d=10,
            smooth_d=3
        )
        # 兼容 pandas-ta V0.3.14b 的命名
        kdj_df.rename(
            columns={'STOCHk_7_10_3': 'K', 'STOCHd_7_10_3': 'D'},
            inplace=True
        )
        k_series = kdj_df['K']
        d_series = kdj_df['D']

        # 3. 引入额外的确认指标：EMA 和成交量 (Added)
        # 短期均线（10日EMA）和长期均线（20日EMA）
        df['ema10'] = ta.ema(df['close'], length=10)
        df['ema20'] = ta.ema(df['close'], length=20)

        # 过去5天的平均成交量，用于判断是否放量
        df['vol_ma5'] = ta.sma(df['volume'], length=5)

        # 4. 获取最新的指标值
        k_now, k_prev1, k_prev2 = k_series.iloc[-1], k_series.iloc[-2], k_series.iloc[-3]
        d_now, d_prev1, d_prev2 = d_series.iloc[-1], d_series.iloc[-2], d_series.iloc[-3]

        close_now = df['close'].iloc[-1]
        ema10_now, ema20_now = df['ema10'].iloc[-1], df['ema20'].iloc[-1]
        vol_now, vol_ma5_now = df['volume'].iloc[-1], df['vol_ma5'].iloc[-1]

        # 📈 优化后的多头信号：D趋势向上 + K回调再上穿D + 均线多头排列 + 价格放量 (Multi-confirmation)
        # 提高胜率的关键：增加多个确认条件
        bullish_kdj = (d_now > d_prev1 > d_prev2) and \
                      (k_now > k_prev1 < k_prev2) and \
                      (k_now > d_now) and (k_prev1 < d_prev1)

        # 均线多头排列确认 (added)
        bullish_ma = (ema10_now > ema20_now)

        # 成交量放大确认 (added)
        bullish_volume = (vol_now > vol_ma5_now)

        if bullish_kdj and bullish_ma and bullish_volume:
            return 1

        # 📉 优化后的空头信号：D趋势向下 + K反弹再下穿D + 均线空头排列 + 价格放量
        bearish_kdj = (d_now < d_prev1 < d_prev2) and \
                      (k_now < k_prev1 > k_prev2) and \
                      (k_now < d_now) and (k_prev1 > d_prev1)

        # 均线空头排列确认 (added)
        bearish_ma = (ema10_now < ema20_now)

        # 成交量放大确认 (added)
        bearish_volume = (vol_now > vol_ma5_now)

        if bearish_kdj and bearish_ma and bearish_volume:
            return -1

        return 0

    def create_trading_strategy(self, stock, df, signal):
        """
        创建交易策略对象，支持多头和空头
        signal = 1 做多
        signal = -1 做空
        """
        if len(df) == 0:
            return None

        last_close = df['close'].iloc[-1]
        n_digits = 3 if stock['stock_type'] == 'Fund' else 2

        if signal == 1:
            # 📈 做多策略
            entry_price = last_close
            take_profit = round(last_close * 1.05, n_digits)
            # 止损点更精确：使用前一日的最低价作为止损位
            stop_loss = df['low'].iloc[-2]
            # 确保止损价低于入场价 (added)
            if stop_loss > entry_price:
                stop_loss = round(entry_price * 0.98, n_digits)

        elif signal == -1:
            # 📉 做空策略
            entry_price = last_close
            take_profit = round(last_close * 0.95, n_digits)
            # 止损点更精确：使用前一日的最高价作为止损位
            stop_loss = df['high'].iloc[-2]
            # 确保止损价高于入场价 (added)
            if stop_loss < entry_price:
                stop_loss = round(entry_price * 1.02, n_digits)

        else:
            return None

        # 创建交易策略对象
        strategy = TradingStrategy(
            strategy_name=self.name,
            stock_code=stock['code'],
            stock_name=stock['name'],
            entry_patterns=['ANTI', 'KDJ', 'EMA', 'VOL'] if signal == 1 else [],
            exit_patterns=[],
            exchange=stock['exchange'],
            entry_price=float(entry_price),
            take_profit=float(take_profit),
            stop_loss=float(stop_loss),
            signal=signal
        )
        return strategy

    def get_trading_strategy(self, stock, df):
        """
        根据股票数据和信号生成交易策略
        """
        trading_signal = self.get_trading_signal(stock, df, stock.get('trending', ''), stock.get('direction', ''))
        if trading_signal == 0:
            return None

        strategy = self.create_trading_strategy(stock, df, trading_signal)

        return strategy