from abc import ABC, abstractmethod

from candlestick import get_lower_shadow, get_upper_shadow, get_real_body, is_down, is_upper


class CandlestickPattern(ABC):
    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def match(self, stock, prices):
        pass


class HammerPattern(CandlestickPattern):
    def name(self):
        return '锤子线'

    def match(self, stock, prices):
        price = prices[len(prices) - 1]
        lower_shadow = get_lower_shadow(price)
        upper_shadow = get_upper_shadow(price)
        real_body = get_real_body(price)
        h = lower_shadow + real_body + upper_shadow
        if h == 0:
            return False
        return (lower_shadow / h) > 0.618


class DojiStarPattern(CandlestickPattern):
    def name(self):
        return '十字线'

    def match(self, stock, prices):
        price = prices[len(prices) - 1]
        lower_shadow = get_lower_shadow(price)
        upper_shadow = get_upper_shadow(price)
        real_body = get_real_body(price)
        h = lower_shadow + real_body + upper_shadow
        if h == 0:
            return False
        return lower_shadow >= upper_shadow and (real_body / h) < 0.01


class BullishEngulfingPattern(CandlestickPattern):
    def name(self):
        return '看涨吞没'

    def match(self, stock, prices):
        price = prices[len(prices) - 1]
        pre_price = prices[len(prices) - 2]
        open_price = float(price['open'])
        close_price = float(price['close'])
        pre_high_price = float(pre_price['high'])
        pre_low_price = float(pre_price['low'])
        return is_upper(price) and is_down(pre_price) and close_price >= pre_high_price and open_price <= pre_low_price


class PiercingPattern(CandlestickPattern):
    def name(self):
        return '刺透形态'

    def match(self, stock, prices):
        price = prices[len(prices) - 1]
        pre_price = prices[len(prices) - 2]
        open_price = float(price['open'])
        close_price = float(price['close'])
        pre_open_price = float(pre_price['open'])
        pre_close_price = float(pre_price['close'])
        pre_mid_price = (pre_open_price + pre_close_price) / 2
        return (is_upper(price) and is_down(pre_price)
                and open_price <= pre_close_price and pre_open_price > close_price > pre_mid_price)


class RisingWindowPattern(CandlestickPattern):
    def name(self):
        return '缺口向上'

    def match(self, stock, prices):
        price = prices[len(prices) - 1]
        pre_price = prices[len(prices) - 2]
        low_price = float(price['low'])
        pre_high_price = float(pre_price['high'])
        return low_price > pre_high_price


def get_candlestick_patterns():
    return [HammerPattern(), DojiStarPattern(), BullishEngulfingPattern(), PiercingPattern(), RisingWindowPattern()]
