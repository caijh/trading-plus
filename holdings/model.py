from datetime import datetime

from sqlalchemy import BigInteger, Numeric

from extensions import db
from timezone.zone import CN_TZ


class Holdings(db.Model):
    __tablename__ = "holdings"
    id = db.Column(BigInteger, primary_key=True)
    stock_code = db.Column(db.String(10), unique=True, nullable=False)
    price = db.Column(Numeric(38, 3), nullable=False)
    holding_num = db.Column(Numeric(38, 2), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now(CN_TZ))  # 记录创建时间

    def __repr__(self):
        return f"<Holdings {self.stock_code}, {self.holding_num}@{self.price}>"

    def to_dict(self):
        return {
            "stock_code": self.code,
            "price": self.price,
            "holding_num": self.holding_num,
        }
