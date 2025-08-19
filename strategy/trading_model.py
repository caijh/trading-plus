from calculate.service import calculate_support_resistance, calculate_support_resistance_by_turning_points


class TradingModel:
    def __init__(self, name):
        self.name = name

    @staticmethod
    def get_support_resistance(stock, df):
        (support, resistance) = calculate_support_resistance(stock, df)
        (support_n, resistance_n) = calculate_support_resistance_by_turning_points(stock, df)
        if support_n is not None:
            support = support_n

        if resistance_n is not None:
            resistance = resistance_n
        return support, resistance

    def get_trading_signal(self, stock, df, trending, direction):
        return 0

    def create_trading_strategy(self, stock, df, signal):
        pass

    @staticmethod
    def check_trading_strategy(stock, strategy, max_loss_ratio=0.05):
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

        if (take_profit - entry_price) / (entry_price - stop_loss) < 1:
            return False
        return True

    def get_trading_strategy(self, stock, df):
        return None
