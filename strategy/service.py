from datetime import datetime

from analysis.model import AnalyzedStock
from calculate.service import calculate_trending_direction
from dataset.service import create_dataframe
from extensions import db
from indicator.service import get_candlestick_signal, get_indicator_signal
from stock.service import KType, get_stock_prices
from strategy.model import TradingStrategy
from strategy.trading_exit import get_exit_signal
from strategy.trading_model import TradingModel
from strategy.trading_model_hammer import HammerTradingModel
from strategy.trading_model_index import IndexTradingModel


def add_update_strategy(stock):
    """
    根据给定的股票信息生成交易策略。

    该函数会根据股票的当前信息和市场环境，计算出买入价、止损价等关键指标，并根据这些指标判断是否生成交易策略。
    如果符合条件，则会更新或插入相应的交易策略到数据库中。

    参数:
    - stock (dict): 包含股票详细信息的字典，包括股票代码、名称、阻力位、方向、价格、支撑位等。

    返回:
    无直接返回值，但会根据条件打印相关信息并更新或插入数据库记录。
    """
    with db.session.begin():
        stock_code = stock['code']
        stock_name = stock['name']
        strategy = stock['strategy']

        if strategy is None:
            return None

        strategy = TradingStrategy(
            strategy_name=strategy['strategy_name'],
            stock_code=stock_code,
            stock_name=stock_name,
            exchange=strategy['exchange'],
            entry_patterns=strategy['entry_patterns'],
            entry_price=strategy['entry_price'],
            take_profit=strategy['take_profit'],
            stop_loss=strategy['stop_loss'],
            exit_patterns=strategy['exit_patterns'],
            signal=strategy['signal']
        )
        if not TradingModel.check_trading_strategy(stock, strategy):
            return None

        # 查询是否已存在该股票的交易策略
        existing_strategy = get_strategy_by_stock_code(stock_code)
        if existing_strategy is None:
            db.session.add(strategy)
            db.session.commit()
            print(f"✅ 插入新交易策略：{stock_code} - {stock_name}")
        else:
            print(f"🚀 交易策略：{stock_code} - {stock_name} 已经存在")

        return None


def get_strategy_by_stock_code(stock_code):
    return TradingStrategy.query.filter_by(stock_code=stock_code).first()


def generate_strategies(stocks):
    analyzed_stocks = []
    for stock in stocks:
        if stock['strategy'] is not None and stock['strategy']['signal'] == 1:
            analyzed_stocks.append(stock)

    if len(analyzed_stocks) == 0:
        print("🚀 没有有买入策略的股票")
        return

    print("================================================")
    print(f"🚀 开始生成交易策略，共有{len(analyzed_stocks)}只股票")
    for stock in analyzed_stocks:
        try:
            add_update_strategy(stock)
        except Exception as e:
            print(e)

    print("🚀 交易策略生成完成!!!")


def get_analyzed_stocks():
    """
    获取今天分析的股票信息。

    本函数通过查询数据库中今天创建的 AnalyzedStock 记录来获取股票信息。
    使用 SQLAlchemy ORM 和数据库函数来过滤出今天的记录。

    :return: 今天分析的股票列表
    :rtype: list of AnalyzedStock instances
    """
    # 获取今天的日期
    today = datetime.today().date()
    # 查询数据库中今天创建的 AnalyzedStock 记录
    analyzed_stocks = AnalyzedStock.query.filter(db.func.date(AnalyzedStock.created_at) == today).all()
    # 返回查询结果
    return analyzed_stocks


def check_strategy_reverse_task():
    """
    检查并更新交易策略的任务函数。

    本函数旨在更新数据库中所有交易策略。
    它通过分析股票的最新数据来更新策略的买入价、卖出价和止损价，并设置信号为-1，表示卖出交易信号。
    """

    with db.session.begin():
        # 获取所有交易策略
        strategies = get_trading_strategies()

        # 遍历每个策略进行更新
        for strategy in strategies:
            signal, remark, patterns = get_exit_signal(strategy)
            if signal == -1:
                strategy.signal = -1
                strategy.exit_patterns = patterns
                strategy.remark = remark
                strategy.updated_at = datetime.now()
                print(f'🔄 更新交易策略, 股票名称: {strategy.stock_name}, 股票代码: {strategy.stock_code}')

        # 提交数据库会话，保存所有更新
        db.session.commit()

    # 打印任务完成的日志信息
    print("🚀 check_strategy_reverse_task: 交易策略检查更新完成！")
    return None


def get_trading_strategies():
    """
    获取所有的交易策略。

    此函数通过查询数据库中的TradingStrategy表来获取所有的交易策略。
    它不接受任何参数，并返回一个包含所有交易策略的列表。

    Returns:
        list: 包含所有交易策略的列表。
    """
    # 查询数据库中的所有交易策略
    strategies = TradingStrategy.query.all()
    # 返回查询结果
    return strategies


def run_generate_strategy():
    try:
        # generate_strategy_task()
        check_strategy_reverse_task()
    except Exception as e:
        print(f"Error: {e}")


def analyze_stock(stock, k_type=KType.DAY, strategy_name=None,
                  candlestick_weight=1, ma_weight=1, volume_weight=1):
    print("=====================================================")
    prices = get_stock_prices(stock['code'], k_type)
    if prices is None or len(prices) == 0:
        print(f'No prices get for  stock {stock['code']}')
        return None

    try:
        df = create_dataframe(stock, prices)
        return analyze_stock_prices(stock, df, strategy_name, candlestick_weight, ma_weight, volume_weight)
    except Exception as e:
        print(e)
        return None


def analyze_stock_prices(stock, df, strategy_name=None,
                         candlestick_weight=1, ma_weight=1, volume_weight=1):
    """
    分析股票价格并生成交易策略信号
    
    该函数综合多种技术指标和形态分析，为特定股票生成交易信号和策略。它会计算趋势方向、
    支撑阻力位，并结合K线形态和指标信号来确定交易策略。
    
    Args:
        stock (dict): 股票信息字典，包含股票代码、名称等基本信息
        df (pandas.DataFrame): 股票历史价格数据，包含开盘价、收盘价、最高价、最低价和成交量等列
        strategy_name (str, optional): 指定使用的交易模型名称，默认为None表示使用所有模型
        candlestick_weight (int, optional): K线形态信号权重，默认为1
        ma_weight (int, optional): 均线指标信号权重，默认为1
        volume_weight (int, optional): 成交量指标信号权重，默认为1
        
    Returns:
        TradingStrategy: 生成的交易策略对象，如果未找到合适的策略则返回None
    """
    print("=====================================================")
    print(f'Analyzing Stock, code = {stock['code']}, name = {stock['name']}')

    trading_models = get_trading_models(stock)

    if strategy_name is not None:
        trading_models = [model for model in trading_models if model.name == strategy_name]

    trending, direction = calculate_trending_direction(stock, df)
    stock['trending'] = trending
    stock['direction'] = direction

    support, resistance = TradingModel.get_support_resistance(stock, df)
    stock['support'] = support
    stock['resistance'] = resistance
    stock['price'] = float(df.iloc[-1]['close'])

    candlestick_signal, candlestick_patterns = get_candlestick_signal(stock, df, candlestick_weight)
    stock['candlestick_signal'] = candlestick_signal
    stock['candlestick_patterns'] = [pattern.to_dict() for pattern in candlestick_patterns]

    indicator_signal, primary_patterns, secondary_patterns = get_indicator_signal(stock, df, trending, direction,
                                                                                  ma_weight,
                                                                                  volume_weight)
    stock['indicator_signal'] = indicator_signal
    stock['primary_patterns'] = [pattern.label for pattern in primary_patterns]
    stock['secondary_patterns'] = [pattern.label for pattern in secondary_patterns]

    print(f'code = {stock['code']} candlestick_signal = {candlestick_signal}, indicator_signal = {indicator_signal}')
    strategy = None
    for model in trading_models:
        strategy = model.get_trading_strategy(stock, df)
        if strategy is None:
            continue
        # 检查策略信号是否与K线信号或指标信号匹配
        if candlestick_signal == strategy.signal or indicator_signal == strategy.signal:
            # 根据买卖信号和价格位置判断是否符合策略条件
            stock['strategy'] = strategy.to_dict()

        strategy = None
    signal = 0
    patterns = []
    if strategy is None:
        stock['signal'] = signal
    else:
        signal = strategy.signal
        patterns.extend(strategy.entry_patterns)
    print(
        f'Analyzing Complete code = {stock['code']}, name = {stock['name']}, trending = {stock["trending"]}, direction = {stock["direction"]}, signal= {signal}, patterns = {patterns}, support = {stock["support"]} resistance = {stock["resistance"]} price = {stock["price"]}')
    return strategy


def get_trading_models(stock):
    if stock['stock_type'] == 'Index':
        return [IndexTradingModel()]
    return [
        HammerTradingModel(),
        # AntiTradingModel(),
        # ICTTradingModel(),
        # ZenTradingModel(),
        # AlBrooksProTradingModel(),
        # NTradingModel(),
        # CandlestickIndicatorTradingModel()
    ]
