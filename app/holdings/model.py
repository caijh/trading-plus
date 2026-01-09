from datetime import datetime

from sqlalchemy import BigInteger, Numeric, Column, String, DateTime

from app.core.database import Base


class Holdings(Base):
    __tablename__ = "holdings"
    id = Column(BigInteger, primary_key=True)
    stock_code = Column(String(10), unique=True, nullable=False)
    price = Column(Numeric(38, 3), nullable=False)
    holding_num = Column(Numeric(38, 2), nullable=False)
    created_at = Column(DateTime(), default=datetime.now())  # 记录创建时间
    strategy_id = Column(BigInteger, nullable=True)

    def __repr__(self):
        return f"<Holdings {self.stock_code}, {self.holding_num}@{self.price}>"

    def to_dict(self):
        return {
            "stock_code": self.stock_code,
            "price": self.price,
            "holding_num": self.holding_num,
            "strategy_id": self.strategy_id,
        }
