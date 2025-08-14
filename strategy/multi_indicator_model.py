from calculate.service import calculate_support_resistance, calculate_support_resistance_by_turning_points
from dataset.service import create_dataframe
from environment.service import env_vars
from indicator.candlestick import get_bullish_candlestick_patterns, get_bearish_candlestick_patterns
from indicator.ma import get_up_ma_patterns, get_down_ma_patterns
from stock.service import KType, get_stock_prices
from strategy.model import TradingStrategy
from strategy.trading_model import TradingModel


class MultiIndicatorTradingModel(TradingModel):
    def __init__(self,
                 buy_candlestick_weight=1, buy_ma_weight=2, buy_volume_weight=1,
                 sell_candlestick_weight=0, sell_ma_weight=1, sell_volume_weight=1,
                 ):
        super().__init__('MultiIndicatorTradingModel')
        self.buy_candlestick_weight = buy_candlestick_weight
        self.buy_ma_weight = buy_ma_weight
        self.buy_volume_weight = buy_volume_weight
        self.sell_candlestick_weight = sell_candlestick_weight
        self.sell_ma_weight = sell_ma_weight
        self.sell_volume_weight = sell_volume_weight

    def get_trading_signal(self, stock, df, signal):
        candlestick_patterns, ma_patterns = get_patterns(signal)
        matched_candlestick_patterns, candlestick_weight = get_match_patterns(candlestick_patterns, stock,
                                                                              df, 'candlestick')
        if signal == 1:
            if candlestick_weight >= self.buy_candlestick_weight:
                matched_ma_patterns, ma_weight, matched_volume_patterns = get_match_ma_patterns(ma_patterns, stock, df,
                                                                                                self.buy_volume_weight)
                if ma_weight >= self.buy_ma_weight and len(matched_volume_patterns) >= self.buy_volume_weight:
                    # 将所有匹配的K线形态、均线和量能模式的标签添加到股票的模式列表中
                    append_matched_pattern_label(matched_candlestick_patterns, stock)
                    append_matched_pattern_label(matched_ma_patterns, stock)
                    append_matched_pattern_label(matched_volume_patterns, stock)
                    return 1
        elif signal == -1:
            matched_ma_patterns, ma_weight, matched_volume_patterns = get_match_ma_patterns(ma_patterns, stock,
                                                                                            df, self.sell_volume_weight)
            if candlestick_weight >= self.sell_candlestick_weight and ma_weight >= self.sell_ma_weight:
                # 同样将所有匹配的模式标签添加到股票的模式列表中
                append_matched_pattern_label(matched_candlestick_patterns, stock)
                append_matched_pattern_label(matched_ma_patterns, stock)
                append_matched_pattern_label(matched_volume_patterns, stock)
                return -1

        return 0

    def get_trading_strategy(self, stock, df, signal):
        (support, resistance) = calculate_support_resistance(stock, df)
        (support_n, resistance_n) = calculate_support_resistance_by_turning_points(stock, df)
        if support_n is not None:
            support = support_n

        if resistance_n is not None:
            resistance = resistance_n

        # 将计算得到的支持位和阻力位添加到股票数据中
        stock['support'] = support
        stock['resistance'] = resistance
        stock['price'] = float(df.iloc[-1]['close'])

        trading_signal = self.get_trading_signal(stock, df, signal)
        stock['signal'] = trading_signal
        if trading_signal == 1:
            strategy = create_strategy(stock)
            if check_strategy(stock, strategy):
                return strategy

        return None


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


def get_match_patterns(patterns, stock, df, pattern_type=''):
    code = stock['code']
    name = stock['name']
    weight = 0
    matched_patterns = []
    try:
        for pattern in patterns:
            if pattern.match(stock, df):
                if pattern_type != 'volume':
                    print(f'{code} {name} Match {pattern.label}')
                weight += pattern.weight
                matched_patterns.append(pattern)
    except Exception as e:
        print(e)
    return matched_patterns, weight


def append_matched_pattern_label(matched_patterns, stock):
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
        stock['patterns'].append(matched_pattern.label)


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


def get_match_ma_patterns(patterns, stock, df, volume_weight_limit=1):
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
            if pattern.match(stock, df):
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
                volume_matched_patterns, volume_weight = get_match_patterns(volume_patterns, stock, df,
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


def create_strategy(stock):
    """
    根据输入股票信息生成交易策略，考虑趋势、止损空间、盈亏比率等。
    """
    # 股票基础信息提取
    stock_code = stock['code']
    stock_name = stock['name']
    trending = stock['trending']
    direction = stock['direction']
    n_digits = 3 if stock['stock_type'] == 'Fund' else 2

    # 原始价格点
    support = stock['support']
    resistance = stock['resistance']
    price = stock['price']
    patterns = stock['patterns']
    exchange = stock['exchange']

    # 动态设置买入价、止损、目标价
    if trending == 'UP':
        if direction == 'UP':
            buy_price = price if float(stock['EMA5']) > price else float(stock['EMA5'])
            buy_price = round(buy_price * 1.005, n_digits)
            stop_loss = round(support * 0.995, n_digits)
            target_price = resistance
        else:
            buy_price = round(support * 1.002, n_digits)
            stop_loss = round(buy_price * 0.98, n_digits)
            target_price = resistance  # 预估反弹目标
    else:
        if direction == 'UP':
            buy_price = price if float(stock['EMA5']) > price else float(stock['EMA5'])
            buy_price = round(buy_price, n_digits)
            stop_loss = round(support, n_digits)
            target_price = resistance
        else:
            buy_price = round(support, n_digits)
            stop_loss = round(buy_price * 0.98, n_digits)
            target_price = resistance  # 预估反弹目标

    loss_ratio = (buy_price - stop_loss) / buy_price
    if loss_ratio < 0.008:  # 小于0.8%止损空间太窄
        stop_loss = round(buy_price * 0.99, n_digits)  # 最少预留1%

    # 超高盈亏比，动态调整目标价：以 3 盈亏比为上限
    profit_ratio = (target_price - buy_price) / (buy_price - stop_loss)
    if profit_ratio > 3:
        target_price = round(4 * buy_price - 3 * stop_loss, n_digits)
    # 创建策略对象
    return TradingStrategy(
        stock_code=stock_code,
        stock_name=stock_name,
        exchange=exchange,
        buy_patterns=patterns,
        buy_price=buy_price,
        take_profit=target_price,
        stop_loss=stop_loss,
        sell_patterns=[],
        signal=1
    )


def check_strategy(stock, strategy, max_loss_ratio=0.05, min_profit_ratio=env_vars.MIN_PROFIT_RATE):
    stock_code = stock['code']
    stock_name = stock['name']
    buy_price = strategy.buy_price
    stop_loss = strategy.stop_loss
    take_profit = strategy.take_profit
    # 止损空间过滤
    loss_ratio = (buy_price - stop_loss) / buy_price
    if loss_ratio > max_loss_ratio:
        print(f"{stock_code} {stock_name} 止损空间过大 ({loss_ratio:.2%})，跳过")
        return False

    # 盈亏比判断
    profit_ratio = (take_profit - buy_price) / (buy_price - stop_loss)
    if profit_ratio < float(min_profit_ratio):
        print(f"{stock_code} {stock_name} 盈亏比 {profit_ratio:.2f} 不满足最小要求，跳过")
        return False

    return True


def analyze_stock(stock, k_type=KType.DAY, signal=1,
                  buy_candlestick_weight=1, sell_candlestick_weight=0,
                  buy_ma_weight=2, sell_ma_weight=1,
                  buy_volume_weight=1, sell_volume_weight=1, prices=None, prices_df=None):
    print("=====================================================")
    code = stock['code']
    name = stock['name']
    stock['patterns'] = []
    stock['patterns_candlestick'] = []
    prices = get_stock_prices(code, k_type) if prices is None else prices
    if prices is None or len(prices) == 0:
        print(f'No prices get for  stock {code}')
        return None
    else:
        print(f'Analyzing Stock, code = {code}, name = {name}')
        df = create_dataframe(stock, prices) if prices_df is None else prices_df

        trading_model = MultiIndicatorTradingModel(buy_candlestick_weight, buy_ma_weight, buy_volume_weight,
                                                   sell_candlestick_weight, sell_ma_weight, sell_volume_weight)
        strategy = trading_model.get_trading_strategy(stock, df, signal)
        stock['strategy'] = strategy
        print(
            f'Analyzing Complete code = {code}, name = {name}, patterns = {stock["patterns"]}, support = {stock["support"]} resistance = {stock["resistance"]} price = {stock["price"]}')
        return strategy
