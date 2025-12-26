from datetime import datetime, timedelta

from dataset.service import create_dataframe
from environment.service import env_vars
from holdings.service import get_holdings
from indicator.service import get_exit_patterns, get_candlestick_signal, get_indicator_signal
from stock.service import get_stock, get_stock_prices, KType
from timezone.zone import CN_TZ


def get_exit_signal(strategy):
    code = strategy.stock_code
    # 根据代码获取股票的最新数据
    stock = get_stock(code)
    # 如果获取失败，则跳过当前策略
    if stock is None:
        return 0, '无法获取股票信息', []
    # 如果没有卖出信号，获取股票的持仓信息
    holdings = get_holdings(code)
    # 如果没有持仓信息
    if holdings is None:
        # 更新太旧策略signal = -1
        print(datetime.now(CN_TZ))
        print(strategy.created_at)
        print(datetime.now(CN_TZ) - strategy.created_at > timedelta(days=env_vars.STRATEGY_RETENTION_DAY))
        if datetime.now(CN_TZ) - strategy.created_at > timedelta(days=env_vars.STRATEGY_RETENTION_DAY):
            return -1, '策略太久未执行', []
    else:
        prices = get_stock_prices(code, KType.DAY)
        if prices is None or len(prices) == 0:
            print(f'No prices get for  stock {stock['code']}')
            return 0, '无法获取股票价格序列', []
        df = create_dataframe(stock, prices)

        # 是否有提前退出信号
        exit_patterns = get_exit_patterns()
        matched_patterns = []
        for pattern in exit_patterns:
            if pattern.match(stock, df, None, None):
                matched_patterns.append(pattern)
        if len(matched_patterns) > 0:
            labels = []
            for matched_pattern in matched_patterns:
                labels.append(matched_pattern.label)
            return -1, '策略有退出信号', labels

        candlestick_signal, candlestick_patterns = get_candlestick_signal(stock, df, 1)

        indicator_signal, primary_patterns, secondary_patterns = get_indicator_signal(stock, df, None, None,
                                                                                      1,
                                                                                      1)
        if candlestick_signal == -1 and indicator_signal == -1:
            labels = []
            labels.extend([pattern.label for pattern in candlestick_patterns])
            labels.extend([pattern.label for pattern in primary_patterns])
            labels.extend([pattern.label for pattern in secondary_patterns])
            return -1, '策略有退出信号', labels

        price = float(prices[-1])
        if price > float(holdings.price):
            if datetime.now(CN_TZ) - strategy.created_at > timedelta(days=14):
                return -1, '持仓太久卖出', []

    return 0, '继续持有', []
