from datetime import datetime, timedelta, timezone

from analysis.model import AnalyzedStock
from environment.service import env_vars
from extensions import db
from holdings.service import get_holdings
from stock.service import get_stock, KType
from strategy.model import TradingStrategy
from strategy.trading_model import TradingModel
from strategy.trading_model_multi_indicator import analyze_stock


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

        if existing_strategy:
            holdings = get_holdings(stock_code)
            if holdings is None:
                # 没有持仓, 更新已有策略
                existing_strategy.entry_patterns = strategy.entry_patterns
                existing_strategy.exit_patterns = []
                existing_strategy.entry_price = strategy.entry_price
                existing_strategy.take_profit = strategy.take_profit
                existing_strategy.stop_loss = strategy.stop_loss
            else:
                # 如果有持仓信息，则更新卖出信息
                if strategy.take_profit < float(existing_strategy.take_profit):
                    existing_strategy.take_profit = strategy.take_profit
            existing_strategy.signal = 1
            existing_strategy.updated_at = datetime.now()
            print(f"🔄 更新交易策略：{stock_code} - {stock_name}")
        else:
            db.session.add(strategy)
            print(f"✅ 插入新交易策略：{stock_code} - {stock_name}")

        # 提交数据库更改
        db.session.commit()
        return None


def get_strategy_by_stock_code(stock_code):
    return TradingStrategy.query.filter_by(stock_code=stock_code).first()


def generate_strategies(stocks):
    analyzed_stocks = []
    for stock in stocks:
        if stock['strategy'] is not None:
            analyzed_stocks.append(stock)

    if len(analyzed_stocks) == 0:
        print("🚀 没有已经分析的股票")
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
            # 打印正在更新的策略信息
            print(f'更新股票策略, 股票名称: {strategy.stock_name}, 股票代码: {strategy.stock_code}')
            # 获取策略关联的股票代码
            code = strategy.stock_code
            # 根据代码获取股票的最新数据
            stock = get_stock(code)
            # 如果获取失败，则跳过当前策略
            if stock is None:
                continue

            # 分析股票数据，k_type为DAY表示日线图
            new_strategy = analyze_stock(stock, k_type=KType.DAY)
            # 检查分析结果中是否有卖出信号
            if new_strategy is not None and new_strategy.signal == -1:
                # 有卖出信号，更新策略的买入价、卖出价、止损价、信号和更新时间
                strategy.signal = -1
                strategy.exit_patterns = stock['patterns']
                strategy.updated_at = datetime.now(timezone.utc)
            else:
                # 如果没有卖出信号，获取股票的持仓信息
                holdings = get_holdings(code)
                # 如果没有持仓信息
                if holdings is None:
                    # 更新太旧策略signal = -1
                    if datetime.now() - strategy.created_at > timedelta(
                        days=env_vars.STRATEGY_RETENTION_DAY):
                        strategy.updated_at = datetime.now()
                        strategy.signal = -1
                # else:
                #     # 如果有持仓信息，仅更新卖出价
                #     new_take_profit = float(stock['resistance'])
                #     take_profit = float(strategy.take_profit)
                #     entry_price = float(strategy.entry_price)
                #     stop_loss = float(strategy.stop_loss)
                #     if (take_profit > new_take_profit > entry_price) and (
                #         (new_take_profit - entry_price) / (entry_price - stop_loss) > 0):
                #         strategy.take_profit = new_take_profit
                #         strategy.updated_at = datetime.now()
            # 打印更新策略的日志信息
            print(f"🔄 更新交易策略：{code}")

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
