from analysis.model import AnalyzedStock
from extensions import db


def save_analyzed_stocks(stocks):
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
    with db.session.begin():
        for stock in stocks:
            try:
                save_analyzed_stock(stock)
            except Exception as e:
                print(f"处理 stock 出错: {stock['code']}, 错误信息: {e}")
        db.session.commit()


def save_analyzed_stock(stock):
    analyzed_stock = AnalyzedStock(
        code=stock["code"],
        name=stock["name"],
        exchange=stock["exchange"],
        patterns=stock.get("patterns", []),
        support=stock.get("support"),
        resistance=stock.get("resistance"),
        price=stock.get("price", None)
    )
    db.session.add(analyzed_stock)
    print(f"Add {analyzed_stock} to AnalyzedStock")


def get_recent_price(stock, df, price_type, recent):
    if len(df) < recent:
        return None

    recent_df = df.iloc[-recent:]

    if price_type == 'high':
        max_idx = recent_df['high'].idxmax()
        stock['resistance_date'] = max_idx.strftime('%Y-%m-%d %H:%M:%S')
        return float(recent_df.loc[max_idx]['high'])
    elif price_type == 'low':
        min_idx = recent_df['low'].idxmin()
        stock['support_date'] = min_idx.strftime('%Y-%m-%d %H:%M:%S')
        return float(recent_df.loc[min_idx]['low'])

    return None


