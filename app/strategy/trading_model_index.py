import pandas as pd
import pandas_ta as ta

from app.core.logger import logger
from app.dataset.service import create_dataframe
from app.stock.service import get_stock_prices, KType
from app.strategy.model import TradingStrategy
from app.strategy.trading_model import TradingModel


class IndexTradingModel(TradingModel):
    def __init__(self):
        super().__init__('IndexTradingModel')
        self.patterns = []

    def get_trading_signal(self, stock, df, trending, direction):
        index_fund = stock
        index_fund_df = df
        index_no_volume = False
        if stock['code'] == 'NDX.NS':
            index_fund = {
                "code": "QQQ.NS",
                "name": "QQQ",
                "exchange": "NASDAQ",
                "stock_type": "Fund",
                "stock_code": "QQQ"
            }
            index_no_volume = True
        elif stock['code'] == 'SPX.NS':
            index_fund = {
                "code": "SPY.NS",
                "name": "SPY",
                "exchange": "NASDAQ",
                "stock_type": "Fund",
                "stock_code": "SPY"
            }
            index_no_volume = True

        if index_no_volume:
            prices = get_stock_prices(index_fund['code'], KType.DAY)
            if prices is None or len(prices) == 0:
                logger.info(f'No prices get for  stock {index_fund['code']}')
                return 0

            index_fund_df = create_dataframe(index_fund, prices)

        kdj_df = index_fund_df.ta.stoch(high='high', low='low', close='close', k=9, d=3, smooth_d=3)
        kdj_df.rename(columns={'STOCHk_9_3_3': 'K', 'STOCHd_9_3_3': 'D'}, inplace=True)
        rsi_df = ta.rsi(index_fund_df['close'], length=14, signal_indicators=True)  # type: ignore
        rsi_df.rename(columns={'RSI_14': 'RSI'}, inplace=True)  # type: ignore
        wr_df = ta.willr(high=index_fund_df['high'], low=index_fund_df['low'], close=index_fund_df['close'], length=14)

        last_k = kdj_df['K'].iloc[-1]
        last_d = kdj_df['D'].iloc[-1]
        last_rsi = rsi_df['RSI'].iloc[-1]
        last_wr = wr_df.iloc[-1]

        # 超卖
        self.patterns = []
        if last_k < 20 and last_d < 20:
            self.patterns.append('KDJ')
        if last_rsi < 30:
            self.patterns.append('RSI')
        if last_wr < -80:
            self.patterns.append('WR')
        if len(self.patterns) > 0:
            return 1

        # 超买
        self.patterns = []
        if last_k > 80 and last_d > 80:
            self.patterns.append('KDJ')
        if last_rsi > 70:
            self.patterns.append('RSI')
        if last_wr > -20:
            self.patterns.append('WR')
        if len(self.patterns) > 0:
            return -1
        return 0

    def get_trading_strategy(self, stock, df):
        """
        根据股票数据和信号生成交易策略

        参数:
            stock: 股票信息字典，包含股票相关数据
            df: 股票数据DataFrame，包含历史价格等信息

        返回值:
            交易策略对象，如果无交易信号则返回None
        """
        if stock['stock_type'] != 'Index':
            return None
        trading_signal = self.get_trading_signal(stock, df, stock.get('trending', ''), stock.get('direction', ''))
        return self.create_trading_strategy(stock, df, trading_signal)

    def create_trading_strategy(self, stock: dict, df: pd.DataFrame, signal: int):
        stock_code = stock.get('code')
        stock_name = stock.get('name')
        price = stock.get('price')
        support = stock.get('support')
        resistance = stock.get('resistance')
        exchange = stock.get('exchange')
        patterns = self.patterns

        if signal == 1:
            entry_price = price
            target_price = resistance
            stop_loss = support
        elif signal == -1:
            entry_price = price
            target_price = support
            stop_loss = resistance
        else:
            entry_price = None
            target_price = None
            stop_loss = None

        return TradingStrategy(
            strategy_name=self.name,
            stock_code=stock_code,
            stock_name=stock_name,
            exchange=exchange,
            entry_patterns=patterns,
            entry_price=entry_price,
            take_profit=target_price,
            stop_loss=stop_loss,
            exit_patterns=[],
            signal=signal
        )
