from sqlalchemy.orm import Session

from app.holdings.model import Holdings


def get_holdings(code, db: Session):
    return db.query(Holdings).filter_by(stock_code=code).first()
