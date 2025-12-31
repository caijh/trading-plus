from datetime import datetime

from sqlalchemy import Numeric, Column, Integer, String, JSON, DateTime

from app.core.database import Base


class AnalyzedStock(Base):
    __tablename__ = "analyzed_stock"

    id = Column(Integer, primary_key=True)
    code = Column(String(10), index=True, nullable=False)
    exchange = Column(String(10), nullable=False)
    name = Column(String(255), nullable=False)
    patterns = Column(JSON, nullable=True)  # 存储 JSON 格式的技术指标
    support = Column(Numeric(38, 3), nullable=True)
    resistance = Column(Numeric(38, 3), nullable=True)
    price = Column(Numeric(38, 3), nullable=True)
    created_at = Column(DateTime, default=datetime.now())  # 记录创建时间
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())  # 更新时间

    def __repr__(self):
        return f"<AnalyzedStock {self.code} - {self.name}>"
