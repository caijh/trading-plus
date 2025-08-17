from sqlalchemy import Numeric

from extensions import db


class TradingStrategy(db.Model):
    __tablename__ = "trading_strategy"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 主键
    strategy_name = db.Column(db.String(255), nullable=False)
    stock_code = db.Column(db.String(10), nullable=False, index=True)  # 股票代码
    stock_name = db.Column(db.String(255), nullable=False)
    entry_patterns = db.Column(db.JSON, nullable=True)  # 存储 JSON 格式的技术指标
    exchange = db.Column(db.String(10), nullable=False)
    entry_price = db.Column(Numeric(38, 3), nullable=False)  # 买入价格
    take_profit = db.Column(Numeric(38, 3), nullable=True)  # 卖出价格（目标价）
    stop_loss = db.Column(Numeric(38, 3), nullable=True)  # 止损价
    signal = db.Column(db.INTEGER, nullable=False)  # 信号，执行买还是卖出
    exit_patterns = db.Column(db.JSON, nullable=True)  # 存储 JSON 格式的技术指标
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())  # 记录创建时间
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())  # 更新时间

    def __repr__(self):
        return f"<TradingStrategy {self.stock_code} Buy:{self.entry_price} Sell:{self.take_profit} StopLoss:{self.stop_loss}>"

    def to_dict(self):
        return {
            'id': self.id,
            'strategy_name': self.strategy_name,
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'entry_patterns': self.entry_patterns,
            'exchange': self.exchange,
            'entry_price': self.entry_price,
            'take_profit': self.take_profit,
            'stop_loss': self.stop_loss,
            'signal': self.signal,
            'exit_patterns': self.exit_patterns,
        }
