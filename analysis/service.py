from analysis.model import AnalyzedStock
from extensions import db


def write_db(stocks):
    # 把分析过股票插入数据中，根据code删除原有的，再插入AnalyzedStock对应的表中
    with db.session.begin():
        for stock in stocks:
            code = stock["code"]
            db.session.query(AnalyzedStock).filter_by(code=code).delete()
            new_stock = AnalyzedStock(
                code=stock["code"],
                name=stock["name"],
                patterns=stock.get("patterns", []),
                support=stock.get("support"),
                resistance=stock.get("resistance")
            )
            db.session.add(new_stock)
        db.session.commit()
