from datetime import datetime

from analysis.model import AnalyzedStock
from extensions import db
from stock.service import analyze_stock, get_stock, KType
from strategy.model import TradingStrategy


def generate_strategy_task():
    """读取 AnalyzedStock 表中今天的数据，更新或插入交易策略"""
    today = datetime.today().date()

    with db.session.begin():
        # 获取今天的 AnalyzedStock 数据
        analyzed_stocks = AnalyzedStock.query.filter(db.func.date(AnalyzedStock.created_at) == today).all()

        for stock in analyzed_stocks:
            # 计算买入、卖出、止损价格
            buy_price = stock.support
            sell_price = stock.resistance
            stop_loss = round(stock.support * 0.99, 2)

            # 查询是否已存在该股票的交易策略
            existing_strategy = TradingStrategy.query.filter_by(stock_code=stock.code).first()

            if existing_strategy:
                # **更新已有策略**
                existing_strategy.buy_price = buy_price
                existing_strategy.sell_price = sell_price
                existing_strategy.stop_loss = stop_loss
                existing_strategy.signal = 1
                existing_strategy.updated_at = datetime.now()
                print(f"🔄 更新策略：{stock.code}")
            else:
                # **插入新策略**
                new_strategy = TradingStrategy(
                    stock_code=stock.code,
                    buy_price=buy_price,
                    sell_price=sell_price,
                    stop_loss=stop_loss,
                    signal=1
                )
                db.session.add(new_strategy)
                print(f"✅ 插入新策略：{stock.code}")

        db.session.commit()
    print("🚀 交易策略同步完成！")


def check_strategy_reverse_task():
    """
    检查并更新交易策略的任务函数。

    本函数旨在更新数据库中所有交易策略，针对那些更新日期不是今天的策略进行更新。
    它通过分析股票的最新数据来更新策略的买入价、卖出价和止损价，并设置信号为-1，表示卖出交易信号。
    """
    # 获取今天的日期，用于判断策略是否已经更新
    today = datetime.today().date()

    # 开始一个数据库会话
    with db.session.begin():
        # 查询所有更新日期不是今天的交易策略
        strategies = TradingStrategy.query.filter(db.func.date(TradingStrategy.updated_at) != today).all()

        for strategy in strategies:
            # 获取策略关联的股票代码
            code = strategy.stock_code
            # 根据代码获取股票的最新数据
            stock = get_stock(code)
            # 如果获取失败，则跳过当前策略
            if stock is None:
                continue

            # 分析股票数据，k_type为DAY表示日线图，signal为-1表示某种交易信号
            analyze_stock(stock, k_type=KType.DAY, signal=-1)
            # 如果股票数据中没有识别出任何模式，则跳过当前策略
            if len(stock['patterns']) == 0:
                continue

            # **更新已有策略**
            # 更新策略的买入价、卖出价、止损价、信号和更新时间
            strategy.buy_price = stock['support']
            strategy.sell_price = stock['resistance']
            strategy.stop_loss = round(stock['support'] * 0.99, 2)
            strategy.signal = -1
            strategy.updated_at = datetime.now()
            # 打印更新策略的日志信息
            print(f"🔄 更新策略：{stock.code}")

        # 提交数据库会话，保存所有更新
        db.session.commit()

    # 打印任务完成的日志信息
    print("🚀 交易策略同步完成！")
    return None
