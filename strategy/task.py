from datetime import datetime

from analysis.model import AnalyzedStock
from extensions import db
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
            stop_loss = stock.support * 0.98

            # 查询是否已存在该股票的交易策略
            existing_strategy = TradingStrategy.query.filter_by(stock_code=stock.stock_code).first()

            if existing_strategy:
                # **更新已有策略**
                existing_strategy.buy_price = buy_price
                existing_strategy.sell_price = sell_price
                existing_strategy.stop_loss = stop_loss
                existing_strategy.updated_at = datetime.now()
                print(f"🔄 更新策略：{stock.stock_code}")
            else:
                # **插入新策略**
                new_strategy = TradingStrategy(
                    stock_code=stock.stock_code,
                    buy_price=buy_price,
                    sell_price=sell_price,
                    stop_loss=stop_loss
                )
                db.session.add(new_strategy)
                print(f"✅ 插入新策略：{stock.stock_code}")

        db.session.commit()
    print("🚀 交易策略同步完成！")
