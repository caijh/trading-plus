import re
from datetime import timedelta

import pandas as pd

from analysis.service import analyze_stock
from dataset.service import create_dataframe
from indicator.ma import SMA, MACD, SAR, DMI, BIAS, KDJ, RSI, WR
from indicator.volume import VOL, OBV, ADOSC, ADLine, CMF, MFI, VPT
from stock.service import get_stock_prices, get_stock, KType
from strategy.model import TradingStrategy
from strategy.service import creat_strategy


def build_pattern_objects(pattern_names, signal=1):
    pattern_objects = []
    pattern_labels = []

    for name in pattern_names:
        # 提取字母与数字部分（如 SMA10 -> SMA + 10）
        match = re.match(r'([A-Za-z]+)(\d+)?', name)
        if not match:
            continue

        key, param = match.group(1).upper(), match.group(2)
        param = int(param) if param else None
        pattern_labels.append(key)

        if key == "SMA" and param:
            pattern_objects.append(SMA(ma=param, signal=signal))
        elif key == 'MACD':
            pattern_objects.append(MACD(signal=signal))
        elif key == "SAR":
            pattern_objects.append(SAR(signal=signal))
        elif key == 'DMI':
            pattern_objects.append(DMI(signal=signal))
        elif key == "BIAS":
            pattern_objects.append(BIAS(ma=param, bias=-0.09, signal=signal))
        elif key == 'KDJ':
            pattern_objects.append(KDJ(signal=signal))
        elif key == 'RSI':
            pattern_objects.append(RSI(signal=signal))
        elif key == 'WR':
            pattern_objects.append(WR(signal=signal))
        elif key == 'VOL':
            if 'BIAS' in pattern_labels:
                pattern_objects.append(VOL(signal=signal, mode='turning_up'))
            else:
                pattern_objects.append(VOL(signal=signal, mode='any'))
        elif key == "OBV":
            pattern_objects.append(OBV(signal=signal))
        elif key == 'ADOSC':
            pattern_objects.append(ADOSC(signal=signal))
        elif key == "ADLINE":
            pattern_objects.append(ADLine(signal=signal))
        elif key == 'CMF':
            pattern_objects.append(CMF(signal=signal))
        elif key == 'MFI':
            pattern_objects.append(MFI(signal=signal))
        elif key == 'VPT':
            pattern_objects.append(VPT(signal=signal))
        else:
            print(f"未识别的策略名: {name}")

    return pattern_objects


def run_backtest(strategy: TradingStrategy):
    stock = get_stock(strategy.stock_code)
    prices = get_stock_prices(strategy.stock_code)
    df = create_dataframe(stock, prices)
    if df is None or df.empty:
        return []

    patterns = build_pattern_objects(strategy.patterns)
    records = []
    holding = False
    entry_price, entry_time = None, None

    for i in range(len(df)):
        sub_df = df.iloc[:i + 1]
        price = sub_df['close'].iloc[-1]
        time = sub_df.index[-1]

        if not holding:
            if price <= float(strategy.buy_price) and all(p.match(stock, prices, sub_df) for p in patterns):
                entry_price, entry_time = price, time
                holding = True
        else:
            if float(strategy.stop_loss or 0) > 0 and price < float(strategy.stop_loss):
                records.append((entry_time, time, entry_price, price, 'stop_loss'))
                holding = False
            elif float(strategy.sell_price or 0) > 0 and price >= float(strategy.sell_price):
                records.append((entry_time, time, entry_price, price, 'take_profit'))
                holding = False

    return records


def alpha_run_backtest(stock_code):
    stock = get_stock(stock_code)
    prices = get_stock_prices(stock_code)
    df = create_dataframe(stock, prices)
    if df is None or df.empty:
        return []

    records = []
    strategy = None
    holding = False
    entry_price, entry_time = None, None
    start = 20
    for i in range(start, len(df)):
        if strategy is None:
            analyze_stock(stock, k_type=KType.DAY, prices=prices[0: i], prices_df=df.iloc[:i])
            if len(stock['patterns']) > 0:
                strategy = creat_strategy(stock)
                if strategy is not None:
                    strategy.created_at = pd.to_datetime(df.index[i])

        if strategy is None:
            continue

        sub_df = df.iloc[:i + 1]
        price = sub_df['close'].iloc[-1]
        time = sub_df.index[-1]

        if not holding:
            if price < float(strategy.buy_price):
                entry_price, entry_time = price, time
                holding = True

            if not holding and strategy is not None:
                strategy.updated_at = pd.to_datetime(time)
                if strategy.updated_at - strategy.created_at > timedelta(days=9):
                    strategy = None
        else:
            if strategy.signal == -1:
                records.append((entry_time, time, entry_price, price, 'stop_signal'))
                holding = False
                strategy = None
                continue

            if float(strategy.stop_loss or 0) > 0 and price < float(strategy.stop_loss):
                records.append((entry_time, time, entry_price, price, 'stop_loss'))
                holding = False
                strategy = None
            elif float(strategy.sell_price or 0) > 0 and price >= float(strategy.sell_price):
                records.append((entry_time, time, entry_price, price, 'take_profit'))
                holding = False
                strategy = None

            if strategy is not None:
                analyze_stock(stock, k_type=KType.DAY, prices=prices[0: i + 1], prices_df=sub_df, signal=-1)
                if len(stock['patterns']) > 0:
                    strategy.signal = -1

    return records
