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

            analyze_stock(stock, k_type=KType.DAY, strategy_name=strategy.strategy_name, sell_volume_weight=0)
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


def alpha_run_backtest(stock_code, start=21):
    stock = get_stock(stock_code)
    prices = get_stock_prices(stock_code)
    if not prices:
        return []

    df = create_dataframe(stock, prices)
    if df is None or df.empty:
        return []

    records = []
    strategy = None
    holding = False
    entry_price, entry_time = None, None

    for i in range(start, len(df)):
        time = df.index[i]
        row = df.iloc[i]
        low_price, high_price, close_price, open_price = row['low'], row['high'], row['close'], row['open']

        # 更新策略
        if strategy is None:
            _strategy = analyze_stock_prices(stock, df.iloc[:i])
            if _strategy and _strategy.signal == 1:
                strategy = _strategy
                strategy.created_at = pd.to_datetime(time)

        if strategy is None:
            continue

        # 入场逻辑
        if not holding:
            if low_price <= float(strategy.entry_price) <= high_price:
                entry_price, entry_time = float(strategy.entry_price), time
                holding = True

            # 策略过期
            if not holding:
                strategy.updated_at = pd.to_datetime(time)
                if strategy.updated_at - strategy.created_at > timedelta(days=env_vars.STRATEGY_RETENTION_DAY):
                    strategy = None
            continue

        # 持仓中平仓逻辑
        exit_reason = None
        exit_price = close_price

        if strategy.signal == -1:
            exit_price = open_price
            exit_reason = 'stop_signal'
        elif strategy.take_profit and low_price <= float(strategy.take_profit) <= high_price:
            exit_reason = 'take_profit'
        elif strategy.stop_loss and low_price <= float(strategy.stop_loss) <= high_price:
            exit_reason = 'stop_loss'

        if exit_reason:
            records.append((entry_time, time, entry_price, exit_price, exit_reason))
            holding = False
            strategy = None
            continue

        # 更新策略信号
        _strategy = analyze_stock_prices(stock, df.iloc[:i + 1])
        if _strategy and _strategy.signal == -1:
            strategy.signal = -1

    return records
