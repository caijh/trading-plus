import pandas as pd

from dataset.service import create_dataframe
from indicator.service import get_candlestick_signal, get_indicator_signal
from stock.service import get_stock_prices, KType
from strategy.model import TradingStrategy
from strategy.trading_model import TradingModel


class IndexTradingModel(TradingModel):
    def __init__(self,
                 candlestick_weight=1, ma_weight=2, volume_weight=1):
        super().__init__('IndexTradingModel')
        self.candlestick_weight = candlestick_weight
        self.ma_weight = ma_weight
        self.volume_weight = volume_weight
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
                print(f'No prices get for  stock {index_fund['code']}')
                return 0

            index_fund_df = create_dataframe(index_fund, prices)

        candlestick_signal, candlestick_patterns = get_candlestick_signal(index_fund, index_fund_df,
                                                                          self.candlestick_weight)
        if candlestick_signal == 1:
            indicator_signal, ma_patterns, volume_patterns = get_indicator_signal(index_fund, index_fund_df, trending,
                                                                                  direction,
                                                                                  1, self.ma_weight,
                                                                                  self.volume_weight)
            if indicator_signal == 1:
                # 将所有匹配的K线形态、均线和量能模式的标签添加到股票的模式列表中
                add_matched_pattern_label(candlestick_patterns, self.patterns)
                add_matched_pattern_label(ma_patterns, self.patterns)
                add_matched_pattern_label(volume_patterns, self.patterns)
                return 1
        else:
            indicator_signal, ma_patterns, volume_patterns = get_indicator_signal(stock, index_fund_df, trending,
                                                                                  direction, -1,
                                                                                  self.ma_weight,
                                                                                  self.volume_weight)
            if indicator_signal == -1:
                # 将所有匹配的K线形态、均线和量能模式的标签添加到股票的模式列表中
                add_matched_pattern_label(candlestick_patterns, self.patterns)
                add_matched_pattern_label(ma_patterns, self.patterns)
                add_matched_pattern_label(volume_patterns, self.patterns)
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


def add_matched_pattern_label(matched_patterns, patterns):
    """
    将匹配到的模式标签添加到股票信息中。

    遍历匹配到的模式列表，将每个模式的标签添加到指定的股票信息字典中的 'patterns' 键下。

    参数:
    matched_patterns: 匹配到的模式对象列表，每个模式对象包含一个 'label' 属性，用于表示模式的标签。
    stock: 包含股票信息的字典，必须包含一个 'patterns' 键，用于存储模式标签的列表。

    返回:
    无返回值。此函数直接修改传入的股票信息字典。
    """
    # 遍历匹配到的模式列表
    for matched_pattern in matched_patterns:
        print(matched_pattern)
        # 将模式的标签添加到股票信息的 'patterns' 列表中
        patterns.append(matched_pattern.label)
