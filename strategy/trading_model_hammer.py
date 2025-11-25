from calculate.service import get_recent_price, get_distance, is_hammer_strict, is_hangingman_strict
from indicator.candlestick import Candlestick
from strategy.model import TradingStrategy
from strategy.trading_model import TradingModel


def is_support_sma(sma_series, loc, close, low, tolerance=0.002):
    """
    增加 tolerance 参数，默认 0.2%
    """
    if loc < 1: return False  # 边界检查

    latest_sma = sma_series.iloc[loc]
    prev_sma = sma_series.iloc[loc - 1]

    # 判定：
    # 1. 均线向上 (latest > prev)
    # 2. 最低价触及均线范围 (low <= sma * (1 + tolerance))
    # 3. 收盘价在均线之上 (close >= sma) -> 确认支撑有效
    trend_ok = latest_sma > prev_sma
    touch_support = low <= latest_sma * (1 + tolerance)
    support_held = close > latest_sma

    return trend_ok and touch_support and support_held


def is_resistance_sma(sma_series, loc, close, high, tolerance=0.002):
    latest_sma_price = sma_series.iloc[loc]
    prev_sma_price = sma_series.iloc[loc - 1]
    trend_down = latest_sma_price < prev_sma_price
    touch_resistance = high >= latest_sma_price * (1 - tolerance)
    resistance_held = close < latest_sma_price
    return trend_down and touch_resistance and resistance_held
class HammerTradingModel(TradingModel):
    def __init__(self):
        """
        初始化锤子线交易模型。
        """
        super().__init__('HammerTradingModel')

    def get_trading_signal(self, stock, df, trending, direction):
        """
        根据锤子线或上吊线形态，结合均线趋势和成交量判断交易信号。

        参数:
            stock (dict): 股票信息字典，包含股票代码、名称等。
            df (pandas.DataFrame): 包含历史价格数据的 DataFrame，需包含 'close', 'low', 'high', 'SMA20', 'SMA50', 'SMA120' 列。
            trending (str): 当前趋势状态（如 'UP'、'DOWN'）。
            direction (str): 当前方向（'UP' 表示上涨趋势，'DOWN' 表示下跌趋势）。

        返回:
            int: 交易信号：
                - 1 表示多头信号（买入）；
                - -1 表示空头信号（卖出）；
                - 0 表示无信号。
        """
        # ---- 均线准备 ----
        sma20_series = df['SMA20']
        sma50_series = df['SMA50']
        sma120_series = df['SMA120']
        sma200_series = df['SMA200']

        swing_highs = df[df['turning'] == -1]
        swing_lows = df[df['turning'] == 1]
        trend_up = True if len(swing_lows) > 1 and swing_lows.iloc[-1]['low'] > swing_lows.iloc[-2]['low'] else False
        trend_down = True if len(swing_highs) > 1 and swing_highs.iloc[-1]['high'] < swing_highs.iloc[-2][
            'high'] else False
        # ---- Hammer (多头) ----
        candlestick = Candlestick({"name": "hammer", "description": "锤子线", "signal": 1, "weight": 1}, 1)
        if (candlestick.match(stock, df, trending, direction)
            and trend_up
        ):
            latest_swing_high = swing_highs.iloc[-1] if len(swing_highs) > 0 else None
            k = df.loc[candlestick.match_indexes[-1]]
            if (latest_swing_high is not None
                and is_hammer_strict(k)
                # and get_amplitude(k, df) > 1
            ):
                # 获取最后一个匹配的K线标签及其在数据框中的位置
                # 计算两个位置之间的距离
                l = get_distance(df, k, latest_swing_high)
                # 如果距离大于等于3，则进行后续判断
                if l >= 3:
                    close_price = k['close']
                    low_price = k['low']
                    loc = df.index.get_loc(k.name)
                    if is_support_sma(sma20_series, loc, close_price, low_price):
                        return 1
                    if is_support_sma(sma50_series, loc, close_price, low_price):
                        return 1
                    if is_support_sma(sma120_series, loc, close_price, low_price):
                        return 1
                    if is_support_sma(sma200_series, loc, close_price, low_price):
                        return 1
        # ---- Hangingman (空头) ----
        candlestick = Candlestick({"name": "shootingstar", "description": "流星线", "signal": -1, "weight": 0}, -1)
        if (candlestick.match(stock, df, trending, direction)
            and trend_down
        ):
            k = df.loc[candlestick.match_indexes[-1]]
            latest_swing_low = swing_lows.iloc[-1] if len(swing_lows) > 0 else None
            if (latest_swing_low is not None
                and is_hangingman_strict(k)
                # and get_amplitude(k, df) > 1
            ):
                # 计算两个位置之间的距离
                l = get_distance(df, df.loc[candlestick.match_indexes[-1]], latest_swing_low)
                # 如果距离大于等于3，则进行后续判断
                if l >= 3:
                    loc = df.index.get_loc(k.name)
                    close_price = k['close']
                    high_price = k['high']
                    if is_resistance_sma(sma20_series, loc, close_price, high_price):
                        return -1
                    if is_resistance_sma(sma50_series, loc, close_price, high_price):
                        return -1
                    if is_resistance_sma(sma120_series, loc, close_price, high_price):
                        return -1
                    if is_resistance_sma(sma200_series, loc, close_price, high_price):
                        return -1

        return 0

    def create_trading_strategy(self, stock, df, signal):
        """
        根据交易信号生成具体的交易策略，包括入场价、止盈价和止损价。

        参数:
            stock (dict): 股票信息字典，包含股票代码、名称、类型等。
            df (pandas.DataFrame): 包含历史价格数据的 DataFrame。
            signal (int): 交易信号（1 表示多头，-1 表示空头）。

        返回:
            TradingStrategy: 交易策略对象，若信号无效或风控失败则返回 None。
        """
        last_close = df['close'].iloc[-1]
        n_digits = 3 if stock['stock_type'] == 'Fund' else 2

        low_price = get_recent_price(stock, df, 3, 'low')
        high_price = get_recent_price(stock, df, 3, 'high')
        if signal == 1:  # 多头
            stop_loss = low_price
            entry_price = last_close * 0.998
            target_high = stock['resistance']
            take_profit = target_high * 0.998
        elif signal == -1:  # 空头
            stop_loss = high_price
            entry_price = last_close * 1.002
            target_low = stock['support']
            take_profit = target_low * 1.002
        else:
            return None

        # ---- 风控校验 ----
        risk = abs(entry_price - stop_loss)
        if risk <= 0:
            return None

        # ---- 返回策略 ----
        strategy = TradingStrategy(
            strategy_name=self.name,
            stock_code=stock['code'],
            stock_name=stock['name'],
            entry_patterns=['hammer', 'SMA', 'UP'] if signal == 1 else ['shootingstar', 'SMA', 'DOWN'],
            exit_patterns=[],
            exchange=stock['exchange'],
            entry_price=float(round(entry_price, n_digits)),
            take_profit=float(round(take_profit, n_digits)),
            stop_loss=float(round(stop_loss, n_digits)),
            signal=signal
        )
        return strategy
