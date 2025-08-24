import re
from datetime import timedelta

import pandas as pd

from dataset.service import create_dataframe
from environment.service import env_vars
from indicator.adl import ADL
from indicator.adoc import ADOSC
from indicator.adx import ADX
from indicator.bias import BIAS
from indicator.cmf import CMF
from indicator.kdj import KDJ
from indicator.macd import MACD
from indicator.mfi import MFI
from indicator.obv import OBV
from indicator.rsi import RSI
from indicator.sar import SAR
from indicator.sma import SMA
from indicator.vol import VOL
from indicator.vpt import VPT
from indicator.wr import WR
from stock.service import get_stock_prices, get_stock, KType
from strategy.model import TradingStrategy
from strategy.service import analyze_stock, analyze_stock_prices
from strategy.trading_model_multi_indicator import get_match_ma_patterns


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
            pattern_objects.append(ADX(signal=signal))
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
            pattern_objects.append(ADL(signal=signal))
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

    patterns = build_pattern_objects(strategy.entry_patterns)
    records = []
    holding = False
    entry_price, entry_time = None, None
    strategy.signal = 1
    for i in range(len(df)):
        sub_df = df.iloc[:i + 1]
        price = sub_df['close'].iloc[-1]
        time = sub_df.index[-1]

        if not holding:
            if all(p.match(stock, prices[0: i + 1], sub_df) for p in patterns):
                entry_price, entry_time = price, time
                holding = True
        else:
            if strategy.signal == -1:
                if price > entry_price:
                    records.append((entry_time, time, entry_price, price, 'take_profit'))
                    holding = False
                else:
                    records.append((entry_time, time, entry_price, price, 'stop_loss'))
                    holding = False

                strategy.signal = 1
                continue

            analyze_stock(stock, k_type=KType.DAY, sell_volume_weight=0)
            if len(stock['patterns']) > 0:
                strategy.signal = -1

    return records


def run_backtest_patterns(stock_code, entry_patterns, exit_patterns):
    stock = get_stock(stock_code)
    prices = get_stock_prices(stock_code)
    df = create_dataframe(stock, prices)
    if df is None or df.empty:
        return []

    records = []
    holding = False
    entry_price, entry_time = None, None
    for i in range(len(df)):
        sub_df = df.iloc[:i + 1]
        price = sub_df['close'].iloc[-1]
        time = sub_df.index[-1]

        if not holding:
            _, ma_weight, _ = get_match_ma_patterns(entry_patterns, stock, sub_df, None, None, volume_weight_limit=2)
            if ma_weight >= 2:
                entry_price, entry_time = price, time
                holding = True
        else:
            _, ma_weight, _ = get_match_ma_patterns(exit_patterns, stock, sub_df, None, None, volume_weight_limit=1)
            if ma_weight >= 1:
                if price > entry_price:
                    records.append((entry_time, time, entry_price, price, 'take_profit'))
                    holding = False
                else:
                    records.append((entry_time, time, entry_price, price, 'stop_loss'))
                    holding = False

    return records


def alpha_run_backtest(stock_code):
    stock = get_stock(stock_code)
    prices = get_stock_prices(stock_code)
    if not (len(prices) > 0):
        return []
    df = create_dataframe(stock, prices)
    if df is None or df.empty:
        return []

    records = []
    strategy = None
    holding = False
    entry_price, entry_time = None, None
    start = 21
    for i in range(start, len(df)):
        if strategy is None:
            _strategy = analyze_stock_prices(stock, df.iloc[:i])
            if _strategy is not None and _strategy.signal == 1:
                strategy = _strategy
                strategy.created_at = pd.to_datetime(df.index[i])

        if strategy is None:
            continue

        sub_df = df.iloc[:i + 1]
        price = sub_df['close'].iloc[-1]
        low_price = sub_df['low'].iloc[-1]
        high_price = sub_df['high'].iloc[-1]
        time = sub_df.index[-1]

        if not holding:
            if low_price <= float(strategy.entry_price) <= high_price:
                entry_price, entry_time = float(strategy.entry_price), time
                holding = True

            if not holding and strategy is not None:
                strategy.updated_at = pd.to_datetime(time)
                if strategy.updated_at - strategy.created_at > timedelta(days=env_vars.STRATEGY_RETENTION_DAY):
                    strategy = None
        else:
            if strategy.signal == -1:
                price = sub_df['open'].iloc[-1]
                records.append((entry_time, time, entry_price, price, 'stop_signal'))
                holding = False
                strategy = None
                continue

            if float(strategy.take_profit or 0) > 0 and low_price <= float(strategy.take_profit) <= high_price:
                records.append((entry_time, time, entry_price, price, 'take_profit'))
                holding = False
                strategy = None
            elif float(strategy.stop_loss or 0) > 0 and low_price <= float(strategy.stop_loss) <= high_price:
                records.append((entry_time, time, entry_price, price, 'stop_loss'))
                holding = False
                strategy = None

            if strategy is not None:
                _strategy = analyze_stock_prices(stock, df=sub_df)
                if _strategy is not None and _strategy.signal == -1:
                    strategy.signal = -1

    return records
