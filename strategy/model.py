from extensions import db


class TradingStrategy(db.Model):
    __tablename__ = "trading_strategy"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 主键
    stock_code = db.Column(db.String(10), nullable=False, index=True)  # 股票代码
    buy_price = db.Column(db.Float, nullable=False)  # 买入价格
    sell_price = db.Column(db.Float, nullable=True)  # 卖出价格（目标价）
    stop_loss = db.Column(db.Float, nullable=True)  # 止损价
    signal = db.Column(db.INTEGER, nullable=False)  # 信号，执行买还是卖出
    created_at = db.Column(db.DateTime, server_default=db.func.now())  # 记录创建时间
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())  # 更新时间

    def __repr__(self):
        return f"<TradingStrategy {self.stock_code} Buy:{self.buy_price} Sell:{self.sell_price} StopLoss:{self.stop_loss}>"
