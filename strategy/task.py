from datetime import datetime

from analysis.model import AnalyzedStock
from extensions import db
from stock.stock import analyze_stock, get_stock, KType
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
    today = datetime.today().date()

    with db.session.begin():
        strategies = TradingStrategy.query.filter(db.func.date(TradingStrategy.updated_at) != today).all()

        for strategy in strategies:
            code = strategy.stock_code
            stock = get_stock(code)
            if stock is None:
                continue

            analyze_stock(stock, k_type=KType.DAY, signal=-1)
            if len(stock['patterns']) == 0:
                continue

            # **更新已有策略**
            strategy.buy_price = stock['support']
            strategy.sell_price = stock['resistance']
            strategy.stop_loss = round(stock['support'] * 0.99, 2)
            strategy.signal = -1
            strategy.updated_at = datetime.now()
            print(f"🔄 更新策略：{stock.code}")
        db.session.commit()
    print("🚀 交易策略同步完成！")
    return None
