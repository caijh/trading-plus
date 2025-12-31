from datetime import datetime

from sqlalchemy import Numeric, Integer, Column, String, JSON, INTEGER, Text, DateTime

from app.core.database import Base


class TradingStrategy(Base):
    __tablename__ = "trading_strategy"

    id = Column(Integer, primary_key=True, autoincrement=True)  # 主键
    strategy_name = Column(String(255), nullable=False)
    stock_code = Column(String(10), nullable=False, index=True)  # 股票代码
    stock_name = Column(String(255), nullable=False)
    entry_patterns = Column(JSON, nullable=True)  # 存储 JSON 格式的技术指标
    exchange = Column(String(10), nullable=False)
    entry_price = Column(Numeric(38, 3), nullable=False)  # 买入价格
    take_profit = Column(Numeric(38, 3), nullable=True)  # 卖出价格（目标价）
    stop_loss = Column(Numeric(38, 3), nullable=True)  # 止损价
    signal = Column(INTEGER, nullable=False)  # 信号，执行买还是卖出
    exit_patterns = Column(JSON, nullable=True)  # 存储 JSON 格式的技术指标
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime(), default=datetime.now())  # 记录创建时间
    updated_at = Column(DateTime(), default=datetime.now(), onupdate=datetime.now())  # 更新时间

    def __repr__(self):
        return f"<TradingStrategy {self.stock_code} strategyName: {self.strategy_name} signal: {self.signal} Buy:{self.entry_price} Sell:{self.take_profit} StopLoss:{self.stop_loss}>"

    def to_dict(self):
        return {
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
