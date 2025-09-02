from calculate.service import calculate_support_resistance, calculate_support_resistance_by_turning_points
from environment.service import env_vars


class TradingModel:
    def __init__(self, name):
        self.name = name

    @staticmethod
    def get_support_resistance(stock, df):
        """
        计算股票的支撑位和阻力位

        参数:
            stock: 股票代码或股票对象
            df: 包含股票价格数据的DataFrame

        返回:
            tuple: (支撑位, 阻力位) 的元组
        """
        # 计算基于常规方法的支撑位和阻力位
        (support, resistance) = calculate_support_resistance(stock, df)

        # 计算基于转折点的支撑位和阻力位
        (support_n, resistance_n) = calculate_support_resistance_by_turning_points(stock, df)

        # 如果转折点方法计算出了支撑位，则使用转折点的结果
        if support_n is not None:
            support = support_n

        # 如果转折点方法计算出了阻力位，则使用转折点的结果
        if resistance_n is not None:
            resistance = resistance_n

        return support, resistance

    def get_trading_signal(self, stock, df, trending, direction):
        return 0

    def create_trading_strategy(self, stock, df, signal):
        pass

    @staticmethod
    def check_trading_strategy(stock, strategy, max_loss_ratio=0.03):
        entry_price = strategy.entry_price
        stop_loss = strategy.stop_loss
        take_profit = strategy.take_profit
        signal = strategy.signal
        if signal == 1:
            # 止损空间过滤
            loss_ratio = (entry_price - stop_loss) / entry_price
            if loss_ratio > max_loss_ratio:
                print(f"{stock['code']} {stock['name']} 止损空间过大 ({loss_ratio:.2%})，跳过")
                return False
        elif signal == -1:
            # 止损空间过滤
            loss_ratio = (stop_loss - entry_price) / entry_price
            if loss_ratio > max_loss_ratio:
                print(f"{stock['code']} {stock['name']} 止损空间过大 ({loss_ratio:.2%})，跳过")
                return False

        if (take_profit - entry_price) / (entry_price - stop_loss) < env_vars.MIN_PROFIT_RATE:
            return False
        return True

    def get_trading_strategy(self, stock, df):
        """
        根据股票数据和信号生成交易策略

        参数:
            stock: 股票信息字典，包含股票相关数据
            df: 股票数据DataFrame，包含历史价格等信息

        返回值:
            交易策略对象，如果无交易信号则返回None
        """
        trading_signal = self.get_trading_signal(stock, df, stock.get('trending', ''), stock.get('direction', ''))
        if trading_signal == 0:
            return None
        return self.create_trading_strategy(stock, df, trading_signal)
