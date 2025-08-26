import pandas as pd
import pandas_ta as ta

from calculate.service import get_recent_price
from indicator.bias import BIAS
from indicator.candlestick import get_bullish_candlestick_patterns, get_bearish_candlestick_patterns
from indicator.kdj import KDJ
from indicator.macd import MACD
from indicator.rsi import RSI
from indicator.sar import SAR
from indicator.sma import SMA
from indicator.wr import WR
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
        candlestick_patterns, ma_patterns = get_patterns(1)
        matched_candlestick_patterns, candlestick_weight = get_match_patterns(candlestick_patterns, stock, df, trending,
                                                                              direction, 'candlestick')
        if candlestick_weight >= self.buy_candlestick_weight:
            matched_ma_patterns, ma_weight, matched_volume_patterns = get_match_ma_patterns(ma_patterns, stock, df,
                                                                                            trending, direction,
                                                                                            self.buy_volume_weight)
            if ma_weight >= self.buy_ma_weight:
                # 将所有匹配的K线形态、均线和量能模式的标签添加到股票的模式列表中
                append_matched_pattern_label(matched_candlestick_patterns, self.patterns)
                append_matched_pattern_label(matched_ma_patterns, self.patterns)
                append_matched_pattern_label(matched_volume_patterns, self.patterns)
                return 1

        candlestick_patterns, ma_patterns = get_patterns(-1)
        matched_candlestick_patterns, candlestick_weight = get_match_patterns(candlestick_patterns, stock, df, trending,
                                                                              direction, 'candlestick')
        matched_ma_patterns, ma_weight, matched_volume_patterns = get_match_ma_patterns(ma_patterns, stock, df,
                                                                                        trending, trending,
                                                                                        self.sell_volume_weight)
        if candlestick_weight >= self.sell_candlestick_weight and ma_weight >= self.sell_ma_weight:
            # 同样将所有匹配的模式标签添加到股票的模式列表中
            append_matched_pattern_label(matched_candlestick_patterns, self.patterns)
            append_matched_pattern_label(matched_ma_patterns, self.patterns)
            append_matched_pattern_label(matched_volume_patterns, self.patterns)
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

    def get_trading_strategy(self, stock, df):
        signal = self.get_trading_signal(stock, df, stock['trending'], stock['direction'])
        if signal == 0:
            return None
        strategy = self.create_trading_strategy(stock, df, signal)
        return strategy


def get_patterns(signal):
    """
    根据信号获取相应的K线模式、均线模式和成交量模式。

    本函数根据输入的signal值（1或非1），来决定市场是处于上升趋势还是下降趋势，
    然后分别调用对应的函数获取K线模式、均线模式和成交量模式。

    参数:
    signal (int): 市场信号，1代表买入信号，非1代表卖出信号。

    返回:
    tuple: 包含三个元素的元组，分别是K线模式列表、均线模式列表。
    """
    # 根据信号判断市场趋势并获取相应的模式
    if signal == 1:
        # 买入信号的模式
        candlestick_patterns = get_bullish_candlestick_patterns()
        ma_patterns = get_up_ma_patterns()
    else:
        # 卖出信号的模式
        candlestick_patterns = get_bearish_candlestick_patterns()
        ma_patterns = get_down_ma_patterns()

    # 返回获取到的模式
    return candlestick_patterns, ma_patterns


def get_match_patterns(patterns, stock, df, trending, direction, pattern_type=''):
    code = stock['code']
    name = stock['name']
    weight = 0
    matched_patterns = []
    try:
        for pattern in patterns:
            if pattern.match(stock, df, trending, direction):
                if pattern_type != 'volume':
                    print(f'{code} {name} Match {pattern.label}')
                weight += pattern.weight
                matched_patterns.append(pattern)
    except Exception as e:
        print(e)
    return matched_patterns, weight


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


def get_volume_patterns(matched_ma_patterns):
    patterns = []
    pattern_labels = []
    for pattern in matched_ma_patterns:
        volume_patterns = pattern.get_volume_confirm_patterns()
        for volume_pattern in volume_patterns:
            pattern_label = f'${volume_pattern.label}_${volume_pattern.signal}'
            if pattern_label not in pattern_labels:
                patterns.append(volume_pattern)
                pattern_labels.append(pattern_label)

    return patterns


def get_match_ma_patterns(patterns, stock, df, trending, direction, volume_weight_limit=1):
    """
    根据给定的模式列表，筛选出与特定股票匹配的均线模式。

    参数:
    - patterns: 一个包含所有待检测模式的列表。
    - stock: 一个包含股票信息的字典，必须包含'code'和'name'键。
    - prices: 股票价格数据。
    - df: 包含股票数据的DataFrame。
    - volume_weight_limit=1: 体积权重的阈值，用于过滤模式。

    返回:
    - matched_ma_patterns: 与股票匹配的均线模式列表。
    - ma_weight: 匹配模式的总权重。
    - list(matched_volume_patterns): 匹配的成交量模式列表。
    """
    # 提取股票代码和名称
    code = stock['code']
    name = stock['name']

    # 初始化均线权重和匹配的均线模式列表
    ma_weight = 0
    matched_ma_patterns = []

    # 初始化匹配的成交量模式集合，避免重复计数
    matched_volume_patterns = set()
    matched_volume_pattern_labels = set()
    exec_matched_volume_pattern_labels = set()

    try:
        # 遍历所有模式，寻找匹配的均线模式
        for pattern in patterns:
            # 如果当前模式与股票匹配，则进一步检查成交量模式
            if pattern.match(stock, df, trending, direction):
                # 获取当前模式对应的成交量确认模式
                volume_confirm_patterns = pattern.get_volume_confirm_patterns()

                volume_patterns = []
                total_volume_weight = 0
                total_volume_matched_patterns = []
                for volume_pattern in volume_confirm_patterns:
                    if volume_pattern.label not in exec_matched_volume_pattern_labels:
                        volume_patterns.append(volume_pattern)
                    else:
                        total_volume_matched_patterns.append(volume_pattern)
                        total_volume_weight += volume_pattern.weight

                # 检查成交量模式是否匹配，并获取匹配的模式和权重
                volume_matched_patterns, volume_weight = get_match_patterns(volume_patterns, stock, df, trending,
                                                                            direction,
                                                                            'volume')
                for volume_pattern in volume_matched_patterns:
                    if volume_pattern.label not in exec_matched_volume_pattern_labels:
                        exec_matched_volume_pattern_labels.add(volume_pattern.label)
                    total_volume_matched_patterns.append(volume_pattern)

                total_volume_weight += volume_weight
                # 如果成交量权重超过阈值，则认为该模式有效
                if total_volume_weight >= volume_weight_limit:
                    # 打印匹配信息
                    print(f'{code} {name} Match {pattern.label}')

                    # 累加当前模式的权重到总权重
                    ma_weight += pattern.weight

                    # 将当前模式添加到匹配的均线模式列表中
                    matched_ma_patterns.append(pattern)

                    # 将所有匹配的成交量模式标签添加到集合中
                    for volume_pattern in total_volume_matched_patterns:
                        if volume_pattern.label not in matched_volume_pattern_labels:
                            matched_volume_pattern_labels.add(volume_pattern.label)
                            matched_volume_patterns.add(volume_pattern)
    except Exception as e:
        # 捕获并打印任何异常，然后继续执行程序
        print(e)
        pass

    # 返回匹配的均线模式、总权重和匹配的成交量模式列表
    return matched_ma_patterns, ma_weight, list(matched_volume_patterns)


def get_up_ma_patterns():
    """
    创建并返回一个包含常用均线和偏差率模式的列表。

    这个函数初始化了一个列表，包含了不同周期的均线（如5日、10日、20日、60日、200日均线），
    以及一个特定参数的偏差率模式。这些模式用于在金融数据分析中计算和应用各种移动平均线和偏差率指标。
    """
    # 初始化均线和偏差率模式列表
    ma_patterns = [
        SMA(10, 1),
        SMA(21, 1),
        SMA(50, 1),
        MACD(1),
        SAR(1),
        BIAS(20, -0.09, 1),
        KDJ(1),
        RSI(1),
        WR(1)
    ]
    return ma_patterns


def get_down_ma_patterns():
    """
    创建并返回一个包含常用均线和偏差率模式的列表。

    这个函数初始化了一个列表，包含了不同周期的均线（如5日、10日、20日、60日、200日均线），
    以及一个特定参数的偏差率模式。这些模式用于在金融数据分析中计算和应用各种移动平均线和偏差率指标。
    """
    # 初始化均线和偏差率
    ma_patterns = [
        SMA(10, -1),
        SMA(21, -1),
        SMA(50, -1),
        MACD(-1),
        SAR(-1),
        BIAS(20, 0.09, -1),
        KDJ(-1),
        RSI(-1),
        WR(-1)
    ]
    return ma_patterns
