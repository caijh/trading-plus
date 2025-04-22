from holdings.model import Holdings


def get_holdings(code):
    return Holdings.query.filter_by(stock_code=code).first()
