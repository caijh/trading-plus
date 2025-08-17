from calculate.service import get_recent_price
from strategy.model import TradingStrategy
from strategy.trading_model import TradingModel


class AntiTradingModel(TradingModel):
    def __init__(self):
        super().__init__('AntiTradingModel')

    def get_trading_signal(self, stock, df, trending, direction):
        """
        ANTI 策略结合 KD 指标:
        """

        if len(df) < 20:
            return 0

        # 计算 K、D
        kdj_df = df.ta.stoch(
            high='high',
            low='low',
            close='close',
            k=7,
            d=10,
            smooth_d=3
        )
        kdj_df.rename(
            columns={'STOCHk_7_10_3': 'K', 'STOCHd_7_10_3': 'D'},
            inplace=True
        )
        k_series = kdj_df['K']
        d_series = kdj_df['D']

        # 最近几根K、D值
        k_now, k_prev1, k_prev2 = k_series.iloc[-1], k_series.iloc[-2], k_series.iloc[-3]
        d_now, d_prev1, d_prev2 = d_series.iloc[-1], d_series.iloc[-2], d_series.iloc[-3]

        # 📈 多头 ANTI：D趋势向上，K下探后再上升
        if d_now > d_prev1 > d_prev2:  # D线向上
            if (k_prev2 > k_prev1) and (k_now > k_prev1):
                # 先回调再上升
                if k_now > d_now and k_prev1 < d_prev1:
                    # K重新上穿D（确认反弹）
                    return 1

        # 📉 空头 ANTI：D趋势向下，K反弹后再下跌
        if d_now < d_prev1 < d_prev2:  # D线向下
            if (k_prev2 < k_prev1) and (k_now < k_prev1):
                # 先反弹再下跌
                if k_now < d_now and k_prev1 > d_prev1:
                    # K重新下穿D（确认回落）
                    return -1

        return 0

    def create_trading_strategy(self, stock, df, signal):
        """
        创建交易策略对象，支持多头和空头
        signal = 1 做多
        signal = -1 做空
        """
        last_close = df['close'].iloc[-1]
        n_digits = 3 if stock['stock_type'] == 'Fund' else 2

        if signal == 1:
            # 📈 做多策略
            entry_price = last_close
            take_profit = round(last_close * 1.05, n_digits)
            stop_loss = get_recent_price(stock, df, 'low', 2)  # 最近低点作为止损

        elif signal == -1:
            # 📉 做空策略
            entry_price = last_close  # 用 entry_price 存开仓价
            take_profit = round(last_close * 0.95, n_digits)
            stop_loss = get_recent_price(stock, df, 'high', 2)  # 最近高点作为止损

        else:
            return None

        # 创建交易策略对象
        strategy = TradingStrategy(
            strategy_name=self.name,
            stock_code=stock['code'],
            stock_name=stock['name'],
            entry_patterns=['ANTI', 'KD'] if signal == 1 else [],
            exit_patterns=[],
            exchange=stock['exchange'],
            entry_price=entry_price,
            take_profit=take_profit,
            stop_loss=stop_loss,
            signal=signal
        )
        return strategy

    def get_trading_strategy(self, stock, df):
        """
        根据股票数据和信号生成交易策略

        参数:
            stock: 股票信息字典，包含股票的基本信息
            df: 股票价格数据DataFrame，包含历史价格数据
            signal: 交易信号

        返回值:
            TradingStrategy对象或None，如果满足交易条件则返回策略对象，否则返回None
        """
        trading_signal = self.get_trading_signal(stock, df, stock['trending'], stock['direction'])
        if trading_signal == 0:
            return None

        strategy = self.create_trading_strategy(stock, df, trading_signal)

        return strategy
