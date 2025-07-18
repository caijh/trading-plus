from datetime import datetime, timedelta

from analysis.model import AnalyzedStock
from analysis.service import analyze_stock
from environment.service import env_vars
from extensions import db
from holdings.service import get_holdings
from stock.service import get_stock, KType
from strategy.model import TradingStrategy


def generate_strategy(stock):
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
        # 提取股票基本信息
        stock_code = stock['code']
        stock_name = stock['name']
        sell_price = stock['resistance']
        direction = stock['direction']
        buy_price = stock['price']
        stop_loss = stock['support']
        n_digits = 3 if stock['stock_type'] == 'Fund' else 2

        # 根据股票方向调整买入价和止损价
        if "UP" == direction:
            buy_price = round(stock['price'] * 0.99, n_digits)
            stop_loss = round(stock['support'] * 0.99, n_digits)
        elif "DOWN" == direction:
            buy_price = stock['support']
            stop_loss = round(buy_price * env_vars.STOP_LOSS_RATE, n_digits)

        # 检查止损空间是否过小
        if (buy_price - stop_loss) / buy_price < 0.01:
            print(f'{stock_code} {stock_name} 止损空间过小，不生成交易策略')
            return

        # 检查止损空间是否过大
        if (buy_price - stop_loss) / buy_price > 0.05:
            print(f'{stock_code} {stock_name} 止损过大，不生成交易策略')
            return

        # 计算盈利比率并检查是否满足最小盈利比率要求
        profit_rate = round((sell_price - buy_price) / (buy_price - stop_loss), 3)
        if profit_rate < float(env_vars.MIN_PROFIT_RATE):
            print(f'{stock_code} {stock_name} 盈亏比例为{profit_rate}不满足要求，不生成交易策略')
            return

        # 查询是否已存在该股票的交易策略
        existing_strategy = TradingStrategy.query.filter_by(stock_code=stock_code).first()

        if existing_strategy:
            holdings = get_holdings(stock_code)
            if holdings is None:
                # 没有持仓, 更新已有策略
                existing_strategy.patterns = stock['patterns']
                existing_strategy.sell_patterns = []
                existing_strategy.buy_price = buy_price
                existing_strategy.sell_price = sell_price
                existing_strategy.stop_loss = stop_loss
            else:
                # 如果有持仓信息，则更新卖出信息
                if sell_price < float(existing_strategy.sell_price):
                    existing_strategy.sell_price = sell_price
            existing_strategy.signal = 1
            existing_strategy.updated_at = datetime.now()
            print(f"🔄 更新交易策略：{stock_code} - {stock_name}")
        else:
            # 插入新策略
            new_strategy = TradingStrategy(
                stock_code=stock_code,
                stock_name=stock_name,
                exchange=stock['exchange'],
                patterns=stock['patterns'],
                buy_price=buy_price,
                sell_price=sell_price,
                sell_patterns=[],
                stop_loss=stop_loss,
                signal=1
            )
            db.session.add(new_strategy)
            print(f"✅ 插入新交易策略：{stock_code} - {stock_name}")

        # 提交数据库更改
        db.session.commit()


def generate_strategies(stocks):
    analyzed_stocks = stocks

    if len(analyzed_stocks) == 0:
        print("没有已经分析的股票")
        return

    print("================================================")
    print(f"🚀 开始生成交易策略，共有{len(analyzed_stocks)}只股票")
    for stock in analyzed_stocks:
        try:
            generate_strategy(stock)
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

            # 分析股票数据，k_type为DAY表示日线图，signal为-1表示卖出交易信号
            analyze_stock(stock, k_type=KType.DAY, signal=-1)
            # 检查分析结果中是否有卖出信号
            if len(stock['patterns']) > 0:
                # 有卖出信号，更新策略的买入价、卖出价、止损价、信号和更新时间
                strategy.signal = -1
                strategy.sell_patterns = stock['patterns']
                strategy.updated_at = datetime.now()
            else:
                # 如果没有卖出信号，获取股票的持仓信息
                holdings = get_holdings(code)
                # 如果没有持仓信息
                if holdings is None:
                    # 获取最新价格
                    # price = get_stock_price(code)
                    # if price is None:
                    #     print(f'无法获取{code}-{strategy.stock_name}股价')
                    #     continue

                    # 更新策略的买入价、卖出价和止损价
                    # 根据股票类型确定保留的小数位数
                    # n_digits = 3 if stock['stock_type'] == 'Fund' else 2
                    # direction = stock['direction']
                    # if "UP" == direction:
                    #     strategy.buy_price = round(float(price['close']), n_digits)
                    #     strategy.stop_loss = stock['support']
                    # elif "DOWN" == direction:
                    #     strategy.buy_price = stock['support']
                    #     strategy.stop_loss = round(strategy.buy_price * env_vars.STOP_LOSS_RATE, n_digits)
                    # strategy.sell_price = stock['resistance']
                    # 更新时间戳
                    strategy.updated_at = datetime.now()
                    # 更新太旧策略signal = -1
                    if datetime.now() - strategy.created_at > timedelta(days=9):
                        strategy.signal = -1
                    # 盈亏比不够，更新signal = -1
                    # if (strategy.sell_price - strategy.buy_price) / (
                    #     strategy.buy_price - strategy.stop_loss) < float(env_vars.MIN_PROFIT_RATE):
                    #     strategy.signal = -1
                else:
                    # 如果有持仓信息，仅更新卖出价
                    new_sell_price = float(stock['resistance'])
                    sell_price = float(strategy.sell_price)
                    buy_price = float(strategy.buy_price)
                    stop_loss = float(strategy.stop_loss)
                    if (sell_price > new_sell_price > buy_price) and (
                        (new_sell_price - buy_price) / (buy_price - stop_loss) > 0):
                        strategy.sell_price = new_sell_price

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
