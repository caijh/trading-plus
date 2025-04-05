from extensions import db


class AnalyzedStock(db.Model):
    __tablename__ = "analyzed_stock"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    exchange = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    patterns = db.Column(db.JSON, nullable=True)  # 存储 JSON 格式的技术指标
    support = db.Column(db.Float, nullable=True)
    resistance = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())  # 记录创建时间
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())  # 更新时间

    def __repr__(self):
        return f"<AnalyzedStock {self.code} - {self.name}>"

    def to_dict(self):
        return {
            "code": self.code,
            "name": self.name,
            "exchange": self.exchange,
            "patterns": self.patterns,
            "support": self.support,
            "resistance": self.resistance,
        }
