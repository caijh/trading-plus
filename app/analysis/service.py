from sqlalchemy.orm import Session

from app.analysis.model import AnalyzedStock
from app.core.logger import logger


def save_analyzed_stocks(stocks, db: Session):
    """
    将分析过的股票数据插入数据库中。此函数首先根据股票代码删除已存在的股票数据，
    然后将新的股票数据插入到AnalyzedStock表中。

    参数:
    stocks (list): 包含股票数据的列表，每个股票数据是一个字典，包含股票的代码、名称
                   和其他分析数据如模式、支撑位和阻力位。
    """

    if len(stocks) == 0:
        return

    # 把分析过股票插入数据中，根据code删除原有的，再插入AnalyzedStock对应的表中
    with db.begin():
        try:
            for stock in stocks:
                analyzed_stock = AnalyzedStock(
                    code=stock["code"],
                    name=stock["name"],
                    exchange=stock["exchange"],
                    patterns=stock.get("patterns", []),
                    support=stock.get("support"),
                    resistance=stock.get("resistance"),
                    price=stock.get("price", None)
                )
                db.add(analyzed_stock)
                logger.info(f"Add {analyzed_stock} to AnalyzedStock")
            db.commit()
        except Exception as e:
            logger.info(f"处理 stock 出错: {stock['code']}, 错误信息: {e}")


def get_page_analyzed_stocks(db: Session, exchange=None, code=None, page=1, page_size=10):
    query = db.query(AnalyzedStock).order_by(AnalyzedStock.updated_at.desc())
    if exchange:
        query = query.filter_by(exchange=exchange)
    if code:
        query = query.filter_by(code=code)
    total = query.count()
    skip = (page - 1) * page_size
    items = query.offset(skip).limit(page_size).all()
    return {
        "total": total,
        "page_num": (total + page_size - 1) // page_size,
        "page": page,
        "page_size": page_size,
        "has_next": page * page_size < total,
        "has_prev": page > 1,
        "items": [item.__dict__ for item in items]
    }
