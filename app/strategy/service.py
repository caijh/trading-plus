from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.calculate.service import calculate_trending_direction
from app.core.env import STRATEGY_RETENTION_DAY
from app.core.logger import logger
from app.dataset.service import create_dataframe
from app.holdings.service import get_holdings
from app.indicator.service import get_candlestick_signal, get_indicator_signal, get_exit_patterns
from app.stock.service import KType, get_stock_prices, get_stock
from app.strategy.model import TradingStrategy
from app.strategy.trading_model import TradingModel
from app.strategy.trading_model_hammer import HammerTradingModel
from app.strategy.trading_model_index import IndexTradingModel
from app.strategy.trading_model_indicator import IndicatorTradingModel
from app.strategy.trading_model_n import NTradingModel


def add_update_strategy(stock, db: Session):
    """
    根据给定的股票信息生成交易策略。

    该函数会根据股票的当前信息和市场环境，计算出买入价、止损价等关键指标，并根据这些指标判断是否生成交易策略。
    如果符合条件，则会更新或插入相应的交易策略到数据库中。

    参数:
    - stock (dict): 包含股票详细信息的字典，包括股票代码、名称、阻力位、方向、价格、支撑位等。

    返回:
    无直接返回值，但会根据条件打印相关信息并更新或插入数据库记录。
    """
    with db.begin():
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
        existing_strategy = get_strategy_by_stock_code(stock_code, db)
        if existing_strategy is None:
            db.add(strategy)
            db.commit()
            logger.info(f"✅ 插入新交易策略：{stock_code} - {stock_name}")
        else:
            logger.info(f"🚀 交易策略：{stock_code} - {stock_name} 已经存在")

        return None


def get_strategy_by_stock_code(stock_code, db: Session):
    return db.query(TradingStrategy).filter_by(stock_code=stock_code).first()


def generate_strategies(stocks, db):
    analyzed_stocks = []
    for stock in stocks:
        if stock['strategy'] is not None and stock['strategy']['signal'] == 1:
            analyzed_stocks.append(stock)

    if len(analyzed_stocks) == 0:
        logger.info("🚀 没有有买入策略的股票")
        return

    logger.info("================================================")
    logger.info(f"🚀 开始生成交易策略，共有{len(analyzed_stocks)}只股票")
    for stock in analyzed_stocks:
        try:
            add_update_strategy(stock, db)
        except Exception as e:
            logger.info(e, exc_info=True)

    logger.info("🚀 交易策略生成完成!!!")


def check_strategy_reverse_task(db: Session):
    """
    检查并更新交易策略的任务函数。

    本函数旨在更新数据库中所有交易策略。
    它通过分析股票的最新数据来更新策略的买入价、卖出价和止损价，并设置信号为-1，表示卖出交易信号。
    """

    # 获取所有交易策略
    strategies = db.query(TradingStrategy).filter_by(signal=1).all()
    logger.info(f"🚀 共有{len(strategies)}个交易策略")
    with db.begin():
        # 遍历每个策略进行更新
        for strategy in strategies:
            code = strategy.stock_code
            logger.info(f'🚀 检测交易策略, 股票名称: {strategy.stock_name}, 股票代码: {strategy.stock_code}')
            holdings = get_holdings(code, db)
            signal, remark, patterns = get_exit_signal(strategy, holdings)
            if signal == -1:
                strategy.signal = -1
                strategy.exit_patterns = patterns
                strategy.remark = remark
                strategy.updated_at = datetime.now()
                logger.info(f'🔄 更新交易策略, 股票名称: {strategy.stock_name}, 股票代码: {strategy.stock_code}')
        # 提交数据库会话，保存所有更新
        db.commit()
    # 打印任务完成的日志信息
    logger.info("🚀 check_strategy_reverse_task: 交易策略检查更新完成！")
    return None


def get_trading_strategies(db: Session):
    """
    获取所有的交易策略。

    此函数通过查询数据库中的TradingStrategy表来获取所有的交易策略。
    它不接受任何参数，并返回一个包含所有交易策略的列表。

    Returns:
        list: 包含所有交易策略的列表。
    """
    # 查询数据库中的所有交易策略
    strategies = db.query(TradingStrategy).all()
    # 返回查询结果
    return strategies


def run_generate_strategy(_id, db: Session):
    try:
        check_strategy_reverse_task(db)
    except Exception as e:
        db.rollback()
        logger.info(f"Error: {e}", e, exc_info=True)


def analyze_stock(stock, k_type=KType.DAY, strategy_name=None,
                  candlestick_weight=1, ma_weight=1, volume_weight=1):
    logger.info("=====================================================")
    prices = get_stock_prices(stock['code'], k_type)
    if prices is None or len(prices) == 0:
        logger.info(f'No prices get for  stock {stock['code']}')
        return None

    try:
        df = create_dataframe(stock, prices)
        return analyze_stock_prices(stock, df, strategy_name, candlestick_weight, ma_weight, volume_weight)
    except Exception as e:
        logger.info(e, exc_info=True)
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
    logger.info("=====================================================")
    logger.info(f'Analyzing Stock, code = {stock['code']}, name = {stock['name']}')

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
                                                                                  ma_weight, volume_weight)
    stock['indicator_signal'] = indicator_signal
    stock['primary_patterns'] = [pattern.label for pattern in primary_patterns]
    stock['secondary_patterns'] = [pattern.label for pattern in secondary_patterns]

    logger.info(
        f'code = {stock['code']} candlestick_signal = {candlestick_signal}, indicator_signal = {indicator_signal}')
    strategy = None
    for model in trading_models:
        strategy = model.get_trading_strategy(stock, df)
        if strategy is None:
            continue
        # 检查策略信号是否与K线信号或指标信号匹配
        if candlestick_signal == strategy.signal or indicator_signal == strategy.signal:
            # 根据买卖信号和价格位置判断是否符合策略条件
            stock['strategy'] = strategy.to_dict()
            break

        strategy = None
    signal = 0
    patterns = []
    if strategy is None:
        stock['signal'] = signal
    else:
        signal = strategy.signal
        patterns.extend(strategy.entry_patterns)
        stock['patterns'] = patterns
        stock['signal'] = signal
    logger.info(
        f'Analyzing Complete code = {stock['code']}, name = {stock['name']}, trending = {stock["trending"]}, direction = {stock["direction"]}, signal= {signal}, patterns = {patterns}, support = {stock["support"]} resistance = {stock["resistance"]} price = {stock["price"]}')
    return strategy


def get_trading_models(stock):
    if stock['stock_type'] == 'Index':
        return [
            IndexTradingModel(),
            IndicatorTradingModel()
        ]
    return [
        HammerTradingModel(),
        NTradingModel(),
        # AntiTradingModel(),
        # ICTTradingModel(),
        # ZenTradingModel(),
        # AlBrooksProTradingModel(),
        IndicatorTradingModel()
    ]


def get_exit_signal(strategy, holdings):
    code = strategy.stock_code
    stock = get_stock(code)
    # 如果获取失败，则跳过当前策略
    if stock is None:
        return 0, '无法获取股票信息', []

    prices = get_stock_prices(code, KType.DAY)
    if prices is None or len(prices) == 0:
        logger.info(f'No prices get for  stock {stock['code']}')
        return 0, '无法获取股票价格序列', []
    df = create_dataframe(stock, prices)

    # 是否有提前退出信号
    exit_patterns = get_exit_patterns()
    matched_patterns = []
    for pattern in exit_patterns:
        if pattern.match(stock, df, None, None):
            matched_patterns.append(pattern)
    if len(matched_patterns) > 0:
        labels = []
        for matched_pattern in matched_patterns:
            labels.append(matched_pattern.label)
        return -1, '策略有退出信号', labels

    analyze_stock_prices(stock, df)

    candlestick_patterns = stock['candlestick_patterns']
    primary_patterns = stock['primary_patterns']
    secondary_patterns = stock['secondary_patterns']
    if stock['signal'] == -1:
        labels = []
        labels.extend([pattern.label for pattern in candlestick_patterns])
        labels.extend(primary_patterns)
        labels.extend(secondary_patterns)
        return -1, '策略有退出信号', labels

    # 如果没有持仓信息
    if holdings is None:
        # 更新太旧策略signal = -1
        if datetime.now() - strategy.created_at > timedelta(days=STRATEGY_RETENTION_DAY):
            return -1, '策略太久未执行', []
    else:
        price = float(prices[-1]['close'])
        if price > float(holdings.price):
            if datetime.now() - strategy.created_at > timedelta(days=14):
                return -1, '持仓太久卖出', []

    return 0, '继续持有', []
