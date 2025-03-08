def is_upper(price):
    open_price = float(price['open'])
    close_price = float(price['close'])
    return close_price >= open_price


def is_down(price):
    return not is_upper(price)


def get_lower_shadow(price):
    if is_upper(price):
        return float(price['open']) - float(price['low'])
    else:
        return float(price['close']) - float(price['low'])


def get_upper_shadow(price):
    if is_upper(price):
        return float(price['high']) - float(price['close'])
    else:
        return float(price['high']) - float(price['open'])


def get_real_body(price):
    if is_upper(price):
        return float(price['close']) - float(price['open'])
    else:
        return float(price['open']) - float(price['close'])
