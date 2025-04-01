from extensions import db


class AnalyzedStock(db.Model):
    __tablename__ = "analyzed_stock"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    patterns = db.Column(db.JSON, nullable=True)  # 存储 JSON 格式的技术指标
    support = db.Column(db.Float, nullable=True)
    resistance = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f"<AnalyzedStock {self.code} - {self.name}>"

    def to_dict(self):
        return {
            "code": self.code,
            "name": self.name,
            "patterns": self.patterns,
            "support": self.support,
            "resistance": self.resistance,
        }
