from analysis.model import AnalyzedStock
from extensions import db


def write_db(stocks):
    """
    将分析过的股票数据插入数据库中。此函数首先根据股票代码删除已存在的股票数据，
    然后将新的股票数据插入到AnalyzedStock表中。

    参数:
    stocks (list): 包含股票数据的列表，每个股票数据是一个字典，包含股票的代码、名称
                   和其他分析数据如模式、支撑位和阻力位。
    """
    # 开始一个数据库会话
    print(stocks)
    with db.session.begin():
        # 遍历股票列表
        for stock in stocks:
            # 获取股票代码
            code = stock["code"]
            # 删除已存在的相同代码的股票数据
            db.session.query(AnalyzedStock).filter_by(code=code).delete()
            # 创建新的股票数据对象
            new_stock = AnalyzedStock(
                code=stock["code"],
                name=stock["name"],
                patterns=stock.get("patterns", []),
                support=stock.get("support"),
                resistance=stock.get("resistance")
            )
            # 将新的股票数据添加到会话
            db.session.add(new_stock)
        # 提交会话，确保所有更改都保存到数据库中
        db.session.commit()
