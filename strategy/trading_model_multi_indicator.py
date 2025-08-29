import pandas as pd
import pandas_ta as ta

from calculate.service import get_recent_price
from indicator.service import get_candlestick_signal, get_indicator_signal
from stock.constant import Trend, Direction
from strategy.model import TradingStrategy
from strategy.trading_model import TradingModel


class MultiIndicatorTradingModel(TradingModel):
    def __init__(self,
                 buy_candlestick_weight=1, buy_ma_weight=2, buy_volume_weight=1,
                 sell_candlestick_weight=1, sell_ma_weight=1, sell_volume_weight=1,
                 ):
        super().__init__('MultiIndicatorTradingModel')
        self.buy_candlestick_weight = buy_candlestick_weight
        self.buy_ma_weight = buy_ma_weight
        self.buy_volume_weight = buy_volume_weight
        self.sell_candlestick_weight = sell_candlestick_weight
        self.sell_ma_weight = sell_ma_weight
        self.sell_volume_weight = sell_volume_weight
        self.patterns = []

    def get_trading_signal(self, stock, df, trending, direction):
        candlestick_signal, candlestick_patterns = get_candlestick_signal(stock, df, self.buy_candlestick_weight)
        if candlestick_signal == 1:
            indicator_signal, ma_patterns, volume_patterns = get_indicator_signal(stock, df, trending, direction,
                                                                                  1, self.buy_ma_weight,
                                                                                  self.buy_volume_weight)
            if indicator_signal == 1:
                # 将所有匹配的K线形态、均线和量能模式的标签添加到股票的模式列表中
                append_matched_pattern_label(candlestick_patterns, self.patterns)
                append_matched_pattern_label(ma_patterns, self.patterns)
                append_matched_pattern_label(volume_patterns, self.patterns)
                return 1
        else:
            indicator_signal, ma_patterns, volume_patterns = get_indicator_signal(stock, df, trending, direction, -1,
                                                                                  self.sell_ma_weight,
                                                                                  self.sell_volume_weight)
            if indicator_signal == -1:
                # 将所有匹配的K线形态、均线和量能模式的标签添加到股票的模式列表中
                append_matched_pattern_label(candlestick_patterns, self.patterns)
                append_matched_pattern_label(ma_patterns, self.patterns)
                append_matched_pattern_label(volume_patterns, self.patterns)
                return -1

        return 0

    def create_trading_strategy(self, stock: dict, df: pd.DataFrame, signal: int):
        """
        根据股票信息生成交易策略，考虑趋势、方向、止损空间和盈亏比。

        Args:
            stock (dict): 包含股票信息的字典。
            df (pd.DataFrame): 股票历史数据 DataFrame。
            signal (int): 交易信号，1为多头，-1为空头。

        Returns:
            TradingStrategy 或 None
        """
        if signal not in [1, -1]:
            return None

        # 基本信息
        stock_code = stock.get('code')
        stock_name = stock.get('name')
        trending = stock.get('trending', Trend.UNKNOWN)
        direction = stock.get('direction', Direction.SIDE)
        stock_type = stock.get('stock_type', 'Stock')
        n_digits = 3 if stock_type == 'Fund' else 2
        price = stock.get('price')
        ema5_price = float(df.iloc[-1]['EMA5'])
        support = stock.get('support')
        resistance = stock.get('resistance')
        exchange = stock.get('exchange')
        patterns = self.patterns
        sma200_price_now = df.iloc[-1]['SMA200']
        sma200_price_prev = df.iloc[-2]['SMA200']

        if not all([price, support, resistance, ema5_price]):
            return None
        if signal == 1:
            if sma200_price_now < sma200_price_prev:
                return None
        if signal == -1:
            if sma200_price_now > sma200_price_prev:
                return None

        # 最近 swing 拐点
        swing_low = df.loc[df['turning'] == 1, 'low']
        swing_high = df.loc[df['turning'] == -1, 'high']
        recent_low_price = swing_low.iloc[-1] if not swing_low.empty else get_recent_price(stock, df, 3, 'low')
        recent_high_price = swing_high.iloc[-1] if not swing_high.empty else get_recent_price(stock, df, 5, 'high')

        # ATR 用于最小止损
        atr = float(ta.atr(df['high'], df['low'], df['close'], length=14).iloc[-1])

        # 策略模板
        strategy_template = {
            # 顺势交易
            (Trend.UP, Direction.UP): {
                'long': {'entry': min(price, ema5_price) * 1.002, 'stop': support * 0.985,
                         'target': resistance * 0.998},
                'short': {'entry': resistance, 'stop': resistance * 1.01, 'target': support * 1.002},
            },
            (Trend.UP, Direction.DOWN): {
                'long': {'entry': support * 1.001, 'stop': support * 0.985, 'target': resistance * 0.995},
                'short': {'entry': resistance * 0.997, 'stop': resistance * 1.01, 'target': support * 1.002},
            },
            (Trend.DOWN, Direction.UP): {
                'long': {'entry': min(price, ema5_price) * 0.99, 'stop': support * 0.98,
                         'target': resistance * 0.995},
                'short': {'entry': price * 0.997, 'stop': resistance * 1.01, 'target': support * 1.002},
            },
            (Trend.DOWN, Direction.DOWN): {
                'long': {'entry': ema5_price, 'stop': recent_low_price * 0.995,
                         'target': recent_high_price * 1.015},
                'short': {'entry': ema5_price, 'stop': recent_high_price * 1.005,
                          'target': recent_low_price * 0.985},
            },

            # 横盘 / SIDE
            (Trend.SIDE, Direction.UP): {
                'long': {'entry': support * 0.99, 'stop': support * 0.99 * 0.98, 'target': recent_high_price * 0.995},
                'short': {'entry': resistance * 0.998, 'stop': resistance * 1.01, 'target': support * 1.002},
            },
            (Trend.SIDE, Direction.DOWN): {
                'long': {'entry': support * 1.002, 'stop': support * 1.002 * 0.98, 'target': recent_high_price * 0.995},
                'short': {'entry': resistance * 0.998, 'stop': resistance * 0.998 * 1.02, 'target': support * 1.002},
            },
            (Trend.SIDE, Direction.SIDE): {
                'long': {'entry': support * 1.002, 'stop': support * 0.985, 'target': resistance * 0.995},
                'short': {'entry': resistance * 0.998, 'stop': resistance * 1.01, 'target': support * 1.002},
            },

            # UNKNOWN
            (Trend.UNKNOWN, Direction.SIDE): {
                'long': {'entry': support * 1.002, 'stop': support * 0.985, 'target': resistance * 0.995},
                'short': {'entry': resistance * 0.998, 'stop': resistance * 1.01, 'target': support * 1.002},
            },
        }

        strategy_key = (trending, direction)
        if strategy_key not in strategy_template:
            strategy_key = (Trend.SIDE, Direction.SIDE)  # fallback

        strat_type = 'long' if signal == 1 else 'short'
        strat = strategy_template[strategy_key][strat_type]

        entry_price = round(float(strat['entry']), n_digits)
        stop_loss = round(float(strat['stop']), n_digits)
        target_price = round(float(strat['target']), n_digits)

        # 风险控制：最小止损（2%或 ATR*0.4）
        min_stop = atr * 0.4
        if signal == 1:
            stop_loss = min(stop_loss, entry_price - max(entry_price * 0.02, min_stop))
        else:
            stop_loss = max(stop_loss, entry_price + max(entry_price * 0.02, min_stop))

        # 风险控制：最大 RR 4:1
        reward_to_risk = abs(target_price - entry_price) / abs(entry_price - stop_loss)
        if reward_to_risk > 4:
            if signal == 1:
                target_price = round(entry_price + 4 * (entry_price - stop_loss), n_digits)
            else:
                target_price = round(entry_price - 4 * (stop_loss - entry_price), n_digits)

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


def append_matched_pattern_label(matched_patterns, patterns):
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
        # 将模式的标签添加到股票信息的 'patterns' 列表中
        patterns.append(matched_pattern.label)


