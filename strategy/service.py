from datetime import datetime, timedelta

from analysis.model import AnalyzedStock
from analysis.service import analyze_stock
from environment.service import env_vars
from extensions import db
from holdings.service import get_holdings
from stock.service import get_stock, KType
from strategy.model import TradingStrategy


def create_strategy(stock):
    """
    根据输入股票信息生成交易策略，考虑趋势、止损空间、盈亏比率等。
    """
    # 股票基础信息提取
    stock_code = stock['code']
    stock_name = stock['name']
    direction = stock['trending']
    n_digits = 3 if stock['stock_type'] == 'Fund' else 2

    # 原始价格点
    support = stock['support']
    resistance = stock['resistance']
    current_price = stock['price']
    patterns = stock['patterns']
    exchange = stock['exchange']

    # 动态设置买入价、止损、目标价
    if direction == 'UP':
        buy_price = round(current_price * 1.005, n_digits)  # 稍微上突破
        stop_loss = round(support * 0.995, n_digits)  # 支撑下穿一点
        target_price = resistance  # 以阻力为目标
    elif direction == 'DOWN':
        buy_price = round(support * 1.002, n_digits)  # 趋势下跌时尝试抄底
        stop_loss = round(buy_price * 0.95, n_digits)  # 宽松止损
        target_price = resistance  # 预估反弹目标
    else:
        print(f"{stock_code} {stock_name} 趋势不明，跳过")
        return None

    # 止损空间过滤
    loss_ratio = (buy_price - stop_loss) / buy_price
    if loss_ratio < 0.008:  # 小于0.8%止损空间太窄
        stop_loss = round(buy_price * 0.99, n_digits)  # 最少预留1%
        loss_ratio = (buy_price - stop_loss) / buy_price
    if loss_ratio > 0.06:
        print(f"{stock_code} {stock_name} 止损空间过大 ({loss_ratio:.2%})，跳过")
        return None

    # 盈亏比判断
    profit_ratio = (target_price - buy_price) / (buy_price - stop_loss)
    if profit_ratio < float(env_vars.MIN_PROFIT_RATE):
        print(f"{stock_code} {stock_name} 盈亏比 {profit_ratio:.2f} 不满足最小要求，跳过")
        return None

    # 超高盈亏比，动态调整目标价：以 3.5 盈亏比为上限
    if profit_ratio > 3.5:
        target_price = round(buy_price + 3.5 * (buy_price - stop_loss), n_digits)

    # 创建策略对象
    return TradingStrategy(
        stock_code=stock_code,
        stock_name=stock_name,
        exchange=exchange,
        patterns=patterns,
        buy_price=buy_price,
        sell_price=target_price,
        sell_patterns=[],
        stop_loss=stop_loss,
        signal=1
    )


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
        stock_code = stock['code']
        stock_name = stock['name']
        strategy = create_strategy(stock)

        if strategy is None:
            return None

        # 查询是否已存在该股票的交易策略
        existing_strategy = get_strategy_by_stock_code(stock_code)

        if existing_strategy:
            holdings = get_holdings(stock_code)
            if holdings is None:
                # 没有持仓, 更新已有策略
                existing_strategy.patterns = strategy.patterns
                existing_strategy.sell_patterns = []
                existing_strategy.buy_price = strategy.buy_price
                existing_strategy.sell_price = strategy.sell_price
                existing_strategy.stop_loss = strategy.stop_loss
            else:
                # 如果有持仓信息，则更新卖出信息
                if strategy.sell_price < float(existing_strategy.sell_price):
                    existing_strategy.sell_price = strategy.sell_price
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
    analyzed_stocks = stocks

    if len(analyzed_stocks) == 0:
        print("🚀 没有已经分析的股票")
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
                    if datetime.now() - strategy.created_at > timedelta(days=7):
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
