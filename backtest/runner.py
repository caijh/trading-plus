import re

import pandas as pd

from dataset.service import create_dataframe
from environment.service import env_vars
from indicator.primary.bias import BIAS
from indicator.primary.kdj import KDJ
from indicator.primary.macd import MACD
from indicator.primary.rsi import RSI
from indicator.primary.sar import SAR
from indicator.primary.sma import SMA
from indicator.primary.wr import WR
from indicator.secondary.adl import ADL
from indicator.secondary.adoc import ADOSC
from indicator.secondary.adx import ADX
from indicator.secondary.cmf import CMF
from indicator.secondary.mfi import MFI
from indicator.secondary.obv import OBV
from indicator.secondary.vol import VOL
from indicator.secondary.vpt import VPT
from indicator.service import get_exit_patterns
from stock.service import get_stock_prices, get_stock, KType
from strategy.model import TradingStrategy
from strategy.service import analyze_stock, analyze_stock_prices


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

            analyze_stock(stock, k_type=KType.DAY, strategy_name=strategy.strategy_name)
            if len(stock['patterns']) > 0:
                strategy.signal = -1

    return records


def alpha_run_backtest(stock_code, strategy_name, start=61):
    stock = get_stock(stock_code)
    prices = get_stock_prices(stock_code)
    records = []
    win_patterns = []
    loss_patterns = []
    trending_list = []
    direction_list = []
    if not prices:
        return records, win_patterns, loss_patterns, trending_list, direction_list

    df = create_dataframe(stock, prices)
    if df is None or df.empty:
        return records, win_patterns, loss_patterns, trending_list, direction_list

    strategy = None
    holding = False
    entry_price, entry_time = None, None
    trending = None
    direction = None
    strategy_idx = None

    for i in range(start, len(df)):
        time = df.index[i]
        row = df.iloc[i]
        low_price, high_price, close_price, open_price = row['low'], row['high'], row['close'], row['open']

        # 更新策略
        if strategy is None:
            _strategy = analyze_stock_prices(stock, df.iloc[:i], strategy_name)
            if _strategy and _strategy.signal == 1:
                strategy = _strategy
                trending = stock['trending']
                direction = stock['direction']
                strategy.created_at = pd.to_datetime(time)
                strategy_idx = i

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
                if i - strategy_idx > env_vars.STRATEGY_RETENTION_DAY:
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

        strategy.updated_at = pd.to_datetime(time)
        if close_price > entry_price and i - strategy_idx > 10:
            exit_reason = 'stop_holding'

        if exit_reason:
            records.append((entry_time, time, entry_price, exit_price, exit_reason))
            if exit_price > entry_price:
                win_patterns.extend(strategy.entry_patterns)
                win_patterns.append('|')
                trending_list.append("T" + trending)
                direction_list.append("T" + direction)
            if exit_price < entry_price:
                loss_patterns.extend(strategy.entry_patterns)
                loss_patterns.append('|')
                trending_list.append('L' + trending)
                direction_list.append('L' + direction)
            holding = False
            strategy = None
            continue

        # 是否有提前退出信号
        exit_patterns = get_exit_patterns()
        matched_patterns = []
        for pattern in exit_patterns:
            if pattern.match(stock, df.iloc[:i + 1], None, None):
                matched_patterns.append(pattern)
            if len(matched_patterns) > 0:
                strategy.signal = -1

    return records, win_patterns, loss_patterns, trending_list, direction_list
