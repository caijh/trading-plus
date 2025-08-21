from calculate.service import get_recent_price
from dataset.service import create_dataframe
from indicator.bias import BIAS
from indicator.candlestick import get_bullish_candlestick_patterns, get_bearish_candlestick_patterns
from indicator.kdj import KDJ
from indicator.macd import MACD
from indicator.rsi import RSI
from indicator.sar import SAR
from indicator.sma import SMA
from indicator.wr import WR
from stock.service import KType, get_stock_prices
from strategy.model import TradingStrategy
from strategy.trading_model import TradingModel
from strategy.trading_model_anti import AntiTradingModel


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
            if ma_weight >= self.buy_ma_weight and len(matched_volume_patterns) >= 2:
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

    def create_trading_strategy(self, stock, df, signal):
        """
        根据输入股票信息生成交易策略，考虑趋势、止损空间、盈亏比率等。
        """
        if signal not in [1, -1]:
            return None

        # Stock basic information extraction
        stock_code = stock['code']
        stock_name = stock['name']
        trending = stock['trending']
        direction = stock['direction']
        n_digits = 3 if stock['stock_type'] == 'Fund' else 2
        price = stock['price']
        ema5_price = df.iloc[-1]['EMA5']
        entry_price = float(ema5_price)
        support = stock['support']
        resistance = stock['resistance']
        target_price = resistance
        stop_loss = round(entry_price * 0.98, n_digits)
        patterns = self.patterns
        exchange = stock['exchange']
        recent_low_price = get_recent_price(stock, df, 3, 'low')
        recent_high_price = get_recent_price(stock, df, 5, 'high')

        if signal == 1:
            # Define strategies for different trend and direction combinations
            strategies = {
                # Strong Uptrend, Bullish Direction
                ('UP', 'UP'): {
                    'entry_price': round((ema5_price if price > ema5_price else price) * 1.002, n_digits),
                    # Buy the dip
                    'stop_loss': round(support * 0.99, n_digits),
                    'take_profit': resistance,
                },
                # Strong Uptrend, Bearish Direction (potential retracement)
                ('UP', 'DOWN'): {
                    'entry_price': round(support * 1.002, n_digits),  # Buy at support bounce
                    'stop_loss': round(support * 0.98, n_digits),
                    'take_profit': resistance,
                },
                # Weak Uptrend, Bullish Direction
                ('DOWN', 'UP'): {
                    'entry_price': round((ema5_price if price > ema5_price else price) * 0.995, n_digits),
                    # Wait for confirmation of reversal
                    'stop_loss': round(support * 0.98, n_digits),
                    'take_profit': resistance,
                },
                # Weak Uptrend, Bearish Direction (potential retracement)
                ('DOWN', 'DOWN'): {
                    'entry_price': round(ema5_price if price > ema5_price else price, n_digits),
                    # Buy on breakout confirmation
                    'stop_loss': round(recent_low_price, n_digits),
                    'take_profit': round(recent_high_price * 1.02, n_digits),  # Set a realistic profit target
                },
            }

            # Select strategy based on trending and direction
            strategy_key = (trending, direction)
            strategy = strategies.get(strategy_key)
            entry_price = float(strategy['entry_price'])
            stop_loss = float(strategy['stop_loss'])
            target_price = float(strategy['take_profit'])

            # Ensure minimum stop-loss space (at least 2%)
            min_loss_ratio = 0.02
            actual_loss_ratio = (entry_price - stop_loss) / entry_price
            if actual_loss_ratio < min_loss_ratio:
                stop_loss = round(entry_price * (1 - min_loss_ratio), n_digits)

            # Cap the reward-to-risk ratio at 4:1
            reward_to_risk_ratio = (target_price - entry_price) / (entry_price - stop_loss)
            if reward_to_risk_ratio > 4:
                target_price = round(entry_price + 4 * (entry_price - stop_loss), n_digits)

        # Short strategy logic (remains unchanged from original)
        elif signal == -1:
            entry_price = price
            stop_loss = resistance
            target_price = support

        # Create and return the trading strategy object
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


def analyze_stock(stock, k_type=KType.DAY,
                  buy_candlestick_weight=1, sell_candlestick_weight=0,
                  buy_ma_weight=2, sell_ma_weight=1,
                  buy_volume_weight=1, sell_volume_weight=1):
    print("=====================================================")
    prices = get_stock_prices(stock['code'], k_type)
    if prices is None or len(prices) == 0:
        print(f'No prices get for  stock {stock['code']}')
        return None

    df = create_dataframe(stock, prices)
    return analyze_stock_prices(stock, df, buy_candlestick_weight, sell_candlestick_weight,
                                buy_ma_weight, sell_ma_weight,
                                buy_volume_weight, sell_volume_weight)


def analyze_stock_prices(stock, df, buy_candlestick_weight=1, sell_candlestick_weight=0,
                         buy_ma_weight=2, sell_ma_weight=1,
                         buy_volume_weight=1, sell_volume_weight=1):
    print("=====================================================")
    stock['patterns'] = []
    stock['patterns_candlestick'] = []
    print(f'Analyzing Stock, code = {stock['code']}, name = {stock['name']}')

    trading_models = get_trading_models(buy_candlestick_weight, buy_ma_weight, buy_volume_weight,
                                        sell_candlestick_weight, sell_ma_weight, sell_volume_weight)

    support, resistance = TradingModel.get_support_resistance(stock, df)
    stock['support'] = support
    stock['resistance'] = resistance
    stock['price'] = float(df.iloc[-1]['close'])
    stock['signal'] = 0
    strategy = None
    for model in trading_models:
        strategy = model.get_trading_strategy(stock, df)
        if strategy is not None:
            stock['signal'] = strategy.signal
            stock['strategy'] = strategy.to_dict()
            stock['patterns'].extend(strategy.entry_patterns)
            break

    print(
        f'Analyzing Complete code = {stock['code']}, name = {stock['name']}, trending = {stock["trending"]}, direction = {stock["direction"]}, signal= {stock["signal"]}, patterns = {stock["patterns"]}, support = {stock["support"]} resistance = {stock["resistance"]} price = {stock["price"]}')
    return strategy


def get_trading_models(buy_candlestick_weight, buy_ma_weight, buy_volume_weight,
                       sell_candlestick_weight, sell_ma_weight, sell_volume_weight):
    return [
        AntiTradingModel(),
        MultiIndicatorTradingModel(buy_candlestick_weight, buy_ma_weight, buy_volume_weight,
                                   sell_candlestick_weight, sell_ma_weight, sell_volume_weight)
    ]


def get_up_ma_patterns():
    """
    创建并返回一个包含常用均线和偏差率模式的列表。

    这个函数初始化了一个列表，包含了不同周期的均线（如5日、10日、20日、60日、200日均线），
    以及一个特定参数的偏差率模式。这些模式用于在金融数据分析中计算和应用各种移动平均线和偏差率指标。
    """
    # 初始化均线和偏差率模式列表
    ma_patterns = [SMA(10, 1), SMA(20, 1), SMA(50, 1),
                   MACD(1), SAR(1),
                   BIAS(20, -0.09, 1), KDJ(1), RSI(1), WR(1)]
    return ma_patterns


def get_down_ma_patterns():
    """
    创建并返回一个包含常用均线和偏差率模式的列表。

    这个函数初始化了一个列表，包含了不同周期的均线（如5日、10日、20日、60日、200日均线），
    以及一个特定参数的偏差率模式。这些模式用于在金融数据分析中计算和应用各种移动平均线和偏差率指标。
    """
    # 初始化均线和偏差率
    ma_patterns = [SMA(10, -1), SMA(20, -1), SMA(50, -1),
                   MACD(-1), SAR(-1),
                   BIAS(20, 0.09, -1), KDJ(-1), RSI(-1), WR(-1)]
    return ma_patterns
