from environment.service import env_vars
from strategy.model import TradingStrategy


class TradingModel:
    def __init__(self, name):
        self.name = name

    def get_support_resistance(self, stock, df):
        return 0, 0
    def get_trading_signal(self, stock, df, signal):
        return 0

    def create_trading_strategy(self, stock, df):
        """
            根据输入股票信息生成交易策略，考虑趋势、止损空间、盈亏比率等。
            """
        # 股票基础信息提取
        stock_code = stock['code']
        stock_name = stock['name']
        trending = stock['trending']
        direction = stock['direction']
        n_digits = 3 if stock['stock_type'] == 'Fund' else 2

        # 原始价格点
        support = stock['support']
        resistance = stock['resistance']
        price = stock['price']
        patterns = stock['patterns']
        exchange = stock['exchange']

        # 动态设置买入价、止损、目标价
        if trending == 'UP':
            if direction == 'UP':
                buy_price = price if float(stock['EMA5']) > price else float(stock['EMA5'])
                buy_price = round(buy_price, n_digits)
                stop_loss = round(support * 0.995, n_digits)
                target_price = resistance
            else:
                buy_price = round(support, n_digits)
                stop_loss = round(buy_price * 0.98, n_digits)
                target_price = resistance  # 预估反弹目标
        else:
            if direction == 'UP':
                buy_price = price if float(stock['EMA5']) > price else float(stock['EMA5'])
                buy_price = round(buy_price * 0.99, n_digits)
                stop_loss = round(support, n_digits)
                target_price = resistance
            else:
                buy_price = round(support * 0.99, n_digits)
                stop_loss = round(buy_price * 0.98, n_digits)
                target_price = resistance  # 预估反弹目标

        loss_ratio = (buy_price - stop_loss) / buy_price
        if loss_ratio < 0.008:  # 小于0.8%止损空间太窄
            stop_loss = round(buy_price * 0.98, n_digits)  # 最少预留2%

        # 超高盈亏比，动态调整目标价：以 4 盈亏比为上限
        profit_ratio = (target_price - buy_price) / (buy_price - stop_loss)
        if profit_ratio > 4:
            target_price = round(5 * buy_price - 4 * stop_loss, n_digits)
        # 创建策略对象
        return TradingStrategy(
            strategy_name=self.name,
            stock_code=stock_code,
            stock_name=stock_name,
            exchange=exchange,
            buy_patterns=patterns,
            buy_price=buy_price,
            take_profit=target_price,
            stop_loss=stop_loss,
            sell_patterns=[],
            signal=1
        )

    def check_trading_strategy(self, stock, strategy, max_loss_ratio=0.05, min_profit_ratio=env_vars.MIN_PROFIT_RATE):
        stock_code = stock['code']
        stock_name = stock['name']
        buy_price = strategy.buy_price
        stop_loss = strategy.stop_loss
        take_profit = strategy.take_profit
        # 止损空间过滤
        loss_ratio = (buy_price - stop_loss) / buy_price
        if loss_ratio > max_loss_ratio:
            print(f"{stock_code} {stock_name} 止损空间过大 ({loss_ratio:.2%})，跳过")
            return False

        # 盈亏比判断
        # profit_ratio = (take_profit - buy_price) / (buy_price - stop_loss)
        # if profit_ratio < float(min_profit_ratio):
        #     print(f"{stock_code} {stock_name} 盈亏比 {profit_ratio:.2f} 不满足最小要求，跳过")
        #     return False

        return True

    def get_trading_strategy(self, stock, df, signal):
        return None
