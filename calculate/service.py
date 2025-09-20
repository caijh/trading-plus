import numpy as np
import pandas_ta as ta

from stock.constant import Direction, Trend


def detect_turning_point_indexes(series, df=None):
    """
    Detect turning points in a given series with improved accuracy.

    This function identifies both upward and downward turning points by analyzing the slope changes
    in the smoothed version of the series.

    Parameters:
    series (pd.Series): The input series, assumed to be a pandas series.
    window (int): The window size for smoothing the series.
    angle_threshold_degrees_min (float): Minimum angle threshold for acute angles.
    angle_threshold_degrees_max (float): Maximum angle threshold for acute angles.

    Returns:
    tuple: A tuple containing three lists, the first list contains all turning points (upward and downward),
           the second list contains only upward turning points, and the third list contains only downward turning points.
    """
    # Initialize lists to store all turning points, upward turning points, and downward turning points
    turning_points = []
    turning_up_points = []
    turning_down_points = []

    # Iterate through the series, excluding the first and last elements
    start = 1
    step = 1
    series_len = len(series)
    latest_up_point_idx = None
    latest_down_point_idx = None
    for i in range(start, series_len - step):
        # Get the previous, current, and next values
        idx_prev, idx_cur, idx_next = i - step, i, i + step
        prev, curr, next_ = series.iloc[idx_prev], series.iloc[idx_cur], series.iloc[
            idx_next]

        # if curr != 0:
        #     diff = min(abs(prev - curr), abs(next_ - curr)) / curr
        #     if diff < 0.0002:
        #         continue

        # Determine if the current point is an upward turning point
        if prev > curr and curr < next_:
            idx_next_next = idx_next + 2
            if idx_next_next < series_len:
                if latest_up_point_idx is None or (i - latest_up_point_idx) > 3:
                    latest_up_point_idx = i
                    if df is not None:
                        idx, price = _get_recent_price_base_idx(df, latest_up_point_idx, 'low')
                        latest_up_point_idx = idx
                    turning_up_points.append(latest_up_point_idx)
                    turning_points.append(latest_up_point_idx)
                elif i - latest_up_point_idx < 3:
                    if curr <= series.iloc[latest_up_point_idx]:
                        turning_up_points.remove(latest_up_point_idx)
                        turning_points.remove(latest_up_point_idx)
                        latest_up_point_idx = i
                        if df is not None:
                            idx, price = _get_recent_price_base_idx(df, latest_up_point_idx, 'low')
                            latest_up_point_idx = idx
                        turning_up_points.append(latest_up_point_idx)
                        turning_points.append(latest_up_point_idx)
            else:
                latest_up_point_idx = i
                turning_up_points.append(i)
                turning_points.append(i)

        # Determine if the current point is a downward turning point
        if prev < curr and curr > next_:
            idx_prev_prev = idx_prev - 2
            if idx_prev_prev >= 0:
                if latest_down_point_idx is None or (i - latest_down_point_idx) > 3:
                    latest_down_point_idx = i
                    if df is not None:
                        idx, price = _get_recent_price_base_idx(df, latest_down_point_idx, 'high')
                        latest_down_point_idx = idx
                    turning_down_points.append(latest_down_point_idx)
                    turning_points.append(latest_down_point_idx)
                elif i - latest_down_point_idx < 3:
                    if curr >= series.iloc[latest_down_point_idx]:
                        turning_down_points.remove(latest_down_point_idx)
                        turning_points.remove(latest_down_point_idx)
                        latest_down_point_idx = i
                        if df is not None:
                            idx, price = _get_recent_price_base_idx(df, latest_down_point_idx, 'high')
                            latest_down_point_idx = idx
                        turning_down_points.append(latest_down_point_idx)
                        turning_points.append(latest_down_point_idx)
            else:
                latest_down_point_idx = i
                turning_down_points.append(i)
                turning_points.append(i)

    # Return all turning points and the respective upward and downward turning points
    return turning_points, turning_up_points, turning_down_points


def get_round_price(stock, price):
    if price is None:
        return None
    n_digits = 3 if stock.get('stock_type') == 'Fund' else 2
    return round(float(price), n_digits)


def detect_turning_points(series):
    turning_point_idxes, turning_up_point_idxes, turning_down_point_idxes = detect_turning_point_indexes(series)
    turning_points = series.iloc[turning_point_idxes]
    turning_up_points = series.iloc[turning_up_point_idxes]
    turning_down_points = series.iloc[turning_down_point_idxes]
    return turning_points, turning_up_points, turning_down_points


def upping_trending(series):
    turning_points, turning_up_points, turning_down_points = detect_turning_points(series)
    latest = series.iloc[-1]
    prev = series.iloc[-2]

    if len(turning_up_points) < 1:
        return False
    else:
        if len(turning_up_points) >= 2:
            return latest > prev and latest > turning_up_points.iloc[-1] >= turning_up_points.iloc[-2]
        else:
            return latest > prev and latest > turning_up_points.iloc[-1]


def downing_trending(series):
    turning_points, turning_up_points, turning_down_points = detect_turning_points(series)
    latest = series.iloc[-1]
    prev = series.iloc[-2]
    if len(turning_down_points) < 1:
        return False
    else:
        if len(turning_down_points) >= 2:
            return latest < prev and latest < turning_down_points.iloc[-1] <= turning_down_points.iloc[-2]
        else:
            return latest < prev and latest < turning_down_points.iloc[-1]


def calculate_support_resistance(stock, df, window=20, num_std=2):
    """
    计算给定股票的支撑位和阻力位。

    参数:
    - stock: 包含股票信息的字典，至少需要包含股票代码。
    - df: 包含股票历史数据的DataFrame，至少需要包含high, low, close列。

    返回:
    - s: 支撑位，计算结果四舍五入到两位小数。
    - r: 阻力位，计算结果四舍五入到两位小数。
    """
    # 计算 Pivot Points
    df['Pivot'] = (df['high'] + df['low'] + df['close']) / 3
    df['S1'] = 2 * df['Pivot'] - df['high']
    df['R1'] = 2 * df['Pivot'] - df['low']
    df['S2'] = df['Pivot'] - (df['high'] - df['low'])
    df['R2'] = df['Pivot'] + (df['high'] - df['low'])

    # 计算 S3 和 R3（进一步的支撑和阻力水平）
    df['S3'] = df['S2'] - (df['high'] - df['low'])
    df['R3'] = df['R2'] + (df['high'] - df['low'])

    # ========== 计算 Bollinger Bands ==========
    df['MA'] = df['close'].rolling(window).mean()
    df['STD'] = df['close'].rolling(window).std()
    df['Upper'] = df['MA'] + num_std * df['STD']
    df['Lower'] = df['MA'] - num_std * df['STD']

    # 提取最新数据行，用于计算最终的支撑位和阻力位
    latest_data = df.iloc[-1][['Pivot', 'S1', 'R1', 'S2', 'R2', 'S3', 'R3', 'Upper', 'Lower']]

    n_digits = 3 if stock['stock_type'] == 'Fund' else 2
    # 计算最终的支撑位和阻力位
    s = round(float(min(latest_data['S1'], latest_data['S2'], latest_data['S3'])), n_digits)
    r = round(float(max(latest_data['R1'], latest_data['R2'], latest_data['R3'])), n_digits)
    s = round(float(s + latest_data['Lower']) / 2, n_digits)
    r = round(float(r + latest_data['Upper']) / 2, n_digits)

    # # 打印计算结果
    # print(f'{stock["code"]} calculate_support_resistance Support = {s}, Resistance = {r}')

    return s, r


def calculate_trending_direction(stock, df):
    """
    计算趋势 (trending) 和 当前价格方向 (direction)

    trending: 'UP' 表示趋势向上, 'DOWN' 表示趋势向下
    direction: 'UP' 表示当前价格方向向上, 'DOWN' 表示向下
    """

    # 从 df['turning'] 获取拐点索引
    turning_up_idxes = df.index[df['turning'] == 1]
    turning_down_idxes = df.index[df['turning'] == -1]

    # 获取拐点对应的价格
    turning_up_points = df.loc[turning_up_idxes][['close', 'low', 'high', 'open']]
    turning_down_points = df.loc[turning_down_idxes][['close', 'low', 'high', 'open']]

    # 当前价格与均线
    latest_ma_price = df['EMA5'].iloc[-1]
    pre_ma_price = df['EMA5'].iloc[-2]

    # === 当前方向: 结合EMA斜率和价格位置 ===
    if latest_ma_price > pre_ma_price:
        direction = Direction.UP
    elif pre_ma_price > latest_ma_price:
        direction = Direction.DOWN
    else:
        direction = Direction.SIDE  # 横盘或震荡

    # === 趋势判定: 根据拐点高低点结构 ===
    trending = Trend.UNKNOWN
    if len(turning_up_points) > 1 and len(turning_down_points) > 1:
        # up = 低点（lows），down = 高点（highs）
        last_up, prev_up = turning_up_points.iloc[-1], turning_up_points.iloc[-2]  # 低点
        last_down, prev_down = turning_down_points.iloc[-1], turning_down_points.iloc[-2]  # 高点

        # 上升趋势：高点抬高 + 低点抬高
        if last_down['high'] > prev_down['high'] and last_up['low'] > prev_up['low']:
            trending = Trend.UP
        # 下降趋势：高点降低 + 低点降低
        elif last_down['high'] < prev_down['high'] and last_up['low'] < prev_up['low']:
            trending = Trend.DOWN
        else:
            trending = Trend.SIDE

        # 保存最近两个拐点日期
        stock['turning_up_point_1'] = last_up.name.strftime('%Y-%m-%d')
        stock['turning_up_point_2'] = prev_up.name.strftime('%Y-%m-%d')
        stock['turning_down_point_1'] = last_down.name.strftime('%Y-%m-%d')
        stock['turning_down_point_2'] = prev_down.name.strftime('%Y-%m-%d')

    return trending, direction



def calculate_support_resistance_by_turning_points(stock, df, window=5):
    """
    根据均线拐点识别支撑与阻力位

    参数:
    - stock: 股票信息 dict，含 'code'、'stock_type'
    - df: 历史行情数据，含 'close' 列
    - ma_window: 平滑窗口大小

    返回:
    - 支撑位（支撑点中价格 < 当前价格）
    - 阻力位（阻力点中价格 > 当前价格）
    """
    # 只取最近 200 条记录，提升性能并聚焦近期行情
    recent_df = df.tail(200).copy()
    # 平滑价格（可改为 ta.ema(df['close'], ma_window)）
    ma_name = f'EMA{window}'
    if ma_name not in df.columns:
        df[f'{ma_name}'] = ta.ema(recent_df['close'], window).round(3)

    # 找出均线的拐点位置
    # 从 df['turning'] 获取拐点索引
    turning_points_idxes = recent_df.index[recent_df['turning'] != 0]
    turning_up_idxes = recent_df.index[recent_df['turning'] == 1]
    turning_down_idxes = recent_df.index[recent_df['turning'] == -1]

    # 提取拐点价格及索引
    turning_points = recent_df.loc[turning_points_idxes][[f'{ma_name}', 'close', 'low', 'high', 'open']]
    turning_up_points = recent_df.loc[turning_up_idxes][[f'{ma_name}', 'close', 'low', 'high', 'open']]
    turning_down_points = recent_df.loc[turning_down_idxes][[f'{ma_name}', 'close', 'low', 'high', 'open']]

    # 判断当前方向
    upping = True if stock['direction'] == 'UP' else False

    # 支撑点：前低; 阻力点：前高
    current_price = recent_df['close'].iloc[-1]
    supports = turning_down_points[turning_down_points['high'] < current_price]
    resistances = turning_up_points[turning_up_points['low'] > current_price]

    # 找最靠近当前价格的支撑和阻力（按时间最近，取所在K线的低 / 高点）
    support = None
    resistance = None

    # if not supports.empty and support is None:
    #     support = select_nearest_point(stock, recent_df, supports, current_price,field=ma_name, is_support=True)  # 时间上最靠近当前的支撑点
    # else:
    #     support = cal_price_from_ma(stock, recent_df, current_price, is_support=True)
    #
    # if not resistances.empty and resistance is None:
    #     resistance = select_nearest_point(stock, recent_df, resistances, current_price,field=ma_name, is_support=False)
    # else:
    #     resistance = cal_price_from_ma(stock, recent_df, current_price, is_support=False)

    # 如果当前处于上涨趋势，并且存在转折点数据
    if upping and len(turning_points) > 0:
        # 获取最近的两个转折点，用于判断支撑位和阻力位
        first_point = turning_points.iloc[-1]
        second_point = turning_points.iloc[-2] if len(turning_points) > 1 else None
        support_price = None

        # 根据当前价格与均线的关系，计算可能的支撑价格
        if second_point is not None and current_price > second_point[f'{ma_name}']:
            support_price = cal_price_from_kline(stock, recent_df, second_point, current_price, ma_name,
                                                 is_support=True)
        elif current_price > first_point[f'{ma_name}']:
            support_price = cal_price_from_kline(stock, recent_df, first_point, current_price, ma_name, is_support=True)

        # 如果计算出有效的支撑价格，则更新支撑位
        if support_price is not None:
            support = support_price

        # 如果存在阻力位数据且当前未设置阻力位，则选择最近的阻力点
        if not resistances.empty and resistance is None:
            resistance_latest = select_nearest_point(stock, recent_df, resistances, current_price, ma_name,
                                                     is_support=False)
            resistance_score = select_score_point(stock, recent_df, resistances, current_price, ma_name,
                                                  is_support=False)
            # 选取更接近当前价格的阻力位
            resistance_price = resistance_score if resistance_score < resistance_latest else resistance_latest

            # 如果找到有效的阻力价格，则更新阻力位
            if resistance_price is not None:
                resistance = resistance_price

    # 如果不是上涨趋势，但存在转折点数据
    elif len(turning_points) > 0:
        # 如果存在支撑位数据且当前未设置支撑位，则选择最近的支撑点
        if not supports.empty and support is None:
            support_price = select_nearest_point(stock, recent_df, supports, current_price, ma_name,
                                                 is_support=True)
            if support_price is not None:
                support = support_price

        # 获取最近的两个转折点，用于判断阻力位
        first_point = turning_points.iloc[-1]
        second_point = turning_points.iloc[-2] if len(turning_points) > 1 else None
        resistance_price = None

        # 根据当前价格与均线的关系，计算可能的阻力价格
        if second_point is not None and current_price < second_point[f'{ma_name}']:
            resistance_price = cal_price_from_kline(stock, recent_df, second_point, current_price, ma_name,
                                                    is_support=False)
        elif current_price < first_point[f'{ma_name}']:
            resistance_price = cal_price_from_kline(stock, recent_df, first_point, current_price, ma_name,
                                                    is_support=False)

        # 如果计算出有效的阻力价格，则更新阻力位
        if resistance_price is not None:
            resistance = resistance_price

    # 根据基金或股票类型决定小数点保留位数
    s = get_round_price(stock, support)
    r = get_round_price(stock, resistance)

    # 打印计算结果
    # print(
    #     f'{stock["code"]} calculate_support_resistance_by_turning_points Support = {s}, Resistance = {r}, Price = {current_price}')
    return s, r


def cal_price_from_kline(stock, df, point, current_price, field, is_support):
    kline = df.loc[point.name]
    price = kline['high'] if is_support else kline['low']
    # 防止支撑价高于当前价 / 阻力价低于当前价
    if is_support and price > current_price:
        price = kline['low']
        if price > current_price:
            price = kline[f'{field}']
    elif not is_support and price < current_price:
        price = kline['high']
        if price < current_price:
            price = kline[f'{field}']

    formatted_date = point.name.strftime('%Y-%m-%d %H:%M:%S')
    if is_support:
        stock['support_date'] = formatted_date
    else:
        stock['resistance_date'] = formatted_date

    return price


def select_nearest_point(stock, df, points, current_price, field, is_support=True, recent_num=2):
    """
    从最近的候选拐点中，选择价格最接近当前价的点，并返回其所在K线的高/低点。

    参数:
    - df: 原始完整K线数据（含 high / low）
    - points: 候选拐点（DataFrame，含 ma、close）
    - current_price: 当前价格
    - is_support: True 为支撑位，False 为阻力位

    返回:
    - 支撑或阻力价格（float）
    """
    if points.empty:
        return None

    # 按 ma 离当前价格的距离升序排序
    recent_points = points.iloc[-recent_num:]
    recent_points['dist'] = (recent_points[f'{field}'] - current_price).abs()
    point = recent_points.sort_values('dist').iloc[0]
    return cal_price_from_kline(stock, df, point, current_price, field, is_support)


def cal_price_from_ma(stock, df, current_price, is_support):
    """
    根据移动平均线计算目标价格。

    参数:
    stock: 股票对象，用于获取股票相关信息（未在本函数中使用，但可能在上下文中需要）。
    df: DataFrame，包含股票历史数据的表格。
    point: 字符串，表示当前的时间点（未在本函数中使用，但可能在上下文中需要）。
    current_price: 浮点数，当前股票价格。
    is_support: 布尔值，如果为True，则寻找支撑位；如果为False，则寻找压力位。

    返回:
    price: 浮点数，根据移动平均线计算得到的目标价格，如果没有合适的移动平均线价格，则返回None。
    """

    # 初始化目标价格为None
    price = None

    # 获取最新一日的10日、20日、30日移动平均线价格
    latest = df.iloc[-1]
    ma10_price = latest['SMA10']
    ma20_price = latest['SMA20']
    ma50_price = latest['SMA50']
    ma120_price = latest['SMA120']
    ma200_price = latest['SMA200']

    # 根据是否是支撑位来确定目标价格
    if is_support:
        # 如果移动平均线价格低于当前价格，则选择作为支撑位
        if ma10_price < current_price:
            price = ma10_price
            stock['support_date'] = df.index[-1].strftime('%Y-%m-%d %H:%M:%S')
        elif ma20_price < current_price:
            price = ma20_price
            stock['support_date'] = df.index[-1].strftime('%Y-%m-%d %H:%M:%S')
        elif ma50_price < current_price:
            price = ma50_price
            stock['support_date'] = df.index[-1].strftime('%Y-%m-%d %H:%M:%S')
        elif ma120_price < current_price:
            price = ma120_price
            stock['support_date'] = df.index[-1].strftime('%Y-%m-%d %H:%M:%S')
        elif ma200_price < current_price:
            price = ma200_price
            stock['support_date'] = df.index[-1].strftime('%Y-%m-%d %H:%M:%S')
    else:
        # 如果移动平均线价格高于当前价格，则选择作为压力位
        if ma10_price > current_price:
            price = ma10_price
            stock['resistance_date'] = df.index[-1].strftime('%Y-%m-%d %H:%M:%S')
        elif ma20_price > current_price:
            price = ma20_price
            stock['resistance_date'] = df.index[-1].strftime('%Y-%m-%d %H:%M:%S')
        elif ma50_price > current_price:
            price = ma50_price
            stock['resistance_date'] = df.index[-1].strftime('%Y-%m-%d %H:%M:%S')
        elif ma120_price > current_price:
            price = ma120_price
            stock['resistance_date'] = df.index[-1].strftime('%Y-%m-%d %H:%M:%S')
        elif ma200_price > current_price:
            price = ma200_price
            stock['resistance_date'] = df.index[-1].strftime('%Y-%m-%d %H:%M:%S')

    # 返回目标价格
    return price


def select_score_point(stock, df, points, current_price, ma_name, is_support=True):
    """
    从最近的候选拐点中，选择价格最接近当前价的点，并返回其所在K线的高/低点。

    参数:
    - df: 原始完整K线数据（含 high / low）
    - points: 候选拐点（DataFrame，含 ma、close）
    - current_price: 当前价格
    - is_support: True 为支撑位，False 为阻力位

    返回:
    - 支撑或阻力价格（float）
    """
    if points.empty:
        return None

    # 按 ma 离当前价格的距离升序排序
    recent_points = points
    recent_points['score'] = recent_points.index.map(
        lambda idx: score_turning_point(df, idx, current_price, ma_name)['score'])
    point = recent_points.sort_values('score', ascending=False).iloc[0]
    return cal_price_from_kline(stock, df, point, current_price, ma_name, is_support)


def score_turning_point(
    df,
    point_index,
    current_price,
    field,
    window=None,
    slope_window=None,
    price_tolerance=0.005,
    weights=None
):
    """
    计算给定点的转势点得分。

    参数:
    - df: DataFrame, 包含价格和成交量等数据的 DataFrame。
    - point_index: int, 转势点的索引。
    - current_price: float, 当前价格。
    - window: int, 计算窗口大小，默认为数据长度的1/20或5。
    - slope_window: int, 斜率计算窗口大小，默认为数据长度的1/50或3。
    - price_tolerance: float, 价格容忍度，默认为0.005。
    - weights: dict, 各个得分项的权重，默认为{"dist": 0.4, "slope": 0.2, "touch": 0.2, "volume": 0.2}。

    返回:
    - dict: 包含转势点得分和其他相关信息的字典。
    """
    # 初始化权重，如果未提供则使用默认值
    weights = weights or {"dist": 0.5, "slope": 0.1, "touch": 0.1, "volume": 0.3}
    # 计算总权重
    total_weight = sum(weights.values())
    # 检查point_index是否在DataFrame的索引中
    if point_index not in df.index:
        return {"score": 0}
    try:
        # 获取数据长度
        data_len = len(df)
        # 计算或设置窗口大小
        window = window or max(data_len // 20, 5)
        # 计算或设置斜率窗口大小
        slope_window = slope_window or max(data_len // 50, 3)
        # 获取转势点的索引位置
        idx = df.index.get_loc(point_index)
        # 检查索引位置是否在有效范围内
        if idx < window or idx + window >= data_len:
            return {"score": 0}
        # 获取移动平均价系列
        ma_series = df[f'{field}']
        # 获取转势点的价格
        price_at_turn = ma_series.iloc[idx]
        # 计算最大距离
        max_dist = max(abs(df['close'].max() - df['close'].min()), 1e-3)
        # 计算转势点与当前价格的原始距离
        raw_dist = abs(price_at_turn - current_price)
        # 计算距离得分
        dist_score = 1 - min(raw_dist / max_dist, 1)
        # 计算左右斜率
        left_slope = ma_series.iloc[idx] - ma_series.iloc[idx - slope_window]
        right_slope = ma_series.iloc[idx + slope_window] - ma_series.iloc[idx]
        # 计算最大斜率
        max_slope = max(abs(ma_series.max() - ma_series.min()), 1e-6)
        # 计算斜率得分
        slope_score = min(abs(left_slope - right_slope) / max_slope, 1.0)
        # 计算价格容忍范围
        tolerance_range = price_at_turn * price_tolerance
        # 筛选在价格容忍范围内的数据
        touch_df = df[
            (df['close'] >= price_at_turn - tolerance_range) & (df['close'] <= price_at_turn + tolerance_range)]
        # 计算触及次数和触及均量
        touch_count = touch_df.shape[0]
        touch_volume_avg = touch_df['volume'].mean() if not touch_df.empty else 0
        # 计算触及得分
        touch_score = min(touch_count / data_len * (touch_volume_avg / max(df['volume'].median(), 1)), 1.0)
        # 计算成交量的对数
        volume_log = np.log1p(df['volume'])
        # 计算局部成交量对数均值
        local_volume_log = volume_log.iloc[idx - window: idx + window + 1].mean()
        # 计算成交量得分
        volume_score = min(local_volume_log / max(volume_log.median(), 1e-6), 1.0)
        # 计算加权和
        weighted_sum = (
            weights["dist"] * dist_score +
            weights["slope"] * slope_score +
            weights["touch"] * touch_score +
            weights["volume"] * volume_score
        )
        # 计算最终得分
        score = round(weighted_sum / total_weight, 4)
        # 返回结果字典
        return {
            "score": score,
            "point": point_index,
            "dist_score": round(dist_score, 4),
            "slope_score": round(slope_score, 4),
            "touch_score": round(touch_score, 4),
            "volume_score": round(volume_score, 4),
            "price_at_turn": round(price_at_turn, 2),
            "raw_dist": round(raw_dist, 4)
        }
    except Exception as e:
        # 异常处理，打印错误信息并返回0分
        print(f"[score_turning_point] Error at {point_index}: {e}")
        return {"score": 0}


def calculate_vwap_support_resistance(stock, df, window=14, multiplier=2):
    """
    使用滑动VWAP和局部极值法计算股票的支撑位和阻力位。

    参数:
    - stock: dict，包含 'code' 和可选的 'stock_type'
    - df: pd.DataFrame，必须包含 ['date', 'high', 'low', 'close', 'volume']
    - window: int，VWAP与标准差的滚动窗口
    - multiplier: float，偏差放大倍数，用于扩大支撑/阻力区间

    返回:
    - s: 支撑位（四舍五入）
    - r: 阻力位（四舍五入）
    """

    if len(df) < max(60, window):
        print(f"{stock['code']} 数据不足以计算VWAP支撑/阻力")
        return None, None

    # 1. 计算典型价格
    df['Typical_Price'] = (df['high'] + df['low'] + df['close']) / 3

    # 2. 滑动VWAP
    df['TP_Volume'] = df['Typical_Price'] * df['volume']
    df['VWAP'] = df['TP_Volume'].rolling(window=window).sum() / df['volume'].rolling(window=window).sum()

    # 3. 偏差及标准差
    df['Deviation'] = df['Typical_Price'] - df['VWAP']
    df['Deviation_Std'] = df['Deviation'].rolling(window=window).std()

    # 4. 计算支撑阻力
    df['Support'] = df['VWAP'] - multiplier * df['Deviation_Std']
    df['Resistance'] = df['VWAP'] + multiplier * df['Deviation_Std']

    latest = df.iloc[-1]
    s_vwap = latest['Support']
    r_vwap = latest['Resistance']

    n_digits = 3 if stock.get('stock_type') == 'Fund' else 2
    s = round(s_vwap, n_digits)
    r = round(r_vwap, n_digits)

    # 打印计算结果
    print(f'{stock["code"]} calculate_vwap_support_resistance Support = {s}, Resistance = {r}')

    return s, r


def get_recent_price(stock, df, recent, price_type):
    if len(df) < recent:
        return None

    recent_df = df.iloc[-recent:]
    idx, price = _get_recent_price(recent_df, price_type)
    return price


def _get_recent_price(recent_df, price_type):
    if price_type == 'high':
        max_idx = recent_df['high'].idxmax()
        return max_idx, float(recent_df.loc[max_idx]['high'])
    elif price_type == 'low':
        min_idx = recent_df['low'].idxmin()
        return min_idx, float(recent_df.loc[min_idx]['low'])
    return None


def get_recent_price_base_index(df, index, price_type):
    """
    在给定索引前后2个位置（共5个）的K线数据中，
    找出最高价或最低价。

    Args:
        df (pd.DataFrame): 包含'high'和'low'列的股票数据DataFrame。
        index (int): 目标K线的索引。
        price_type (str): 'high' 或 'low'，指定要查找的价格类型。

    Returns:
        float: 指定范围内的最高价或最低价。
    """
    # 确定要切片的范围，确保不超出DataFrame边界
    start_idx = max(0, index - 2)
    end_idx = min(len(df), index + 3)

    # 切片获取子DataFrame
    recent_df = df.iloc[start_idx:end_idx]

    return _get_recent_price(recent_df, price_type)


def _get_recent_price_base_idx(df, idx, price_type):
    """
    在给定索引前后2个位置（共5个）的K线数据中，
    找出最高价或最低价。

    Args:
        df (pd.DataFrame): 包含'high'和'low'列的股票数据DataFrame。
        idx (int): 目标K线的索引。
        price_type (str): 'high' 或 'low'，指定要查找的价格类型。

    Returns:
        float: 指定范围内的最高价或最低价。
    """
    # 确定要切片的范围，确保不超出DataFrame边界
    start_idx = max(0, idx - 3)
    end_idx = min(len(df), idx + 3)

    idx = idx
    if price_type == 'low':
        for i in range(start_idx, end_idx):
            if df.iloc[i]['low'] < df.iloc[idx]['low']:
                idx = i
    elif price_type == 'high':
        for i in range(start_idx, end_idx):
            if df.iloc[i]['high'] > df.iloc[idx]['high']:
                idx = i
    price = df.iloc[idx]['close']
    return idx, price


def get_total_volume_around(df, index, around=3):
    idx = df.index.get_loc(index)
    volume_total = df['volume'].iloc[max(0, idx - around): idx + around].sum()
    return volume_total


def get_avg_volume_around(df, index, around=3):
    return get_total_volume_around(df, index, around) / (2 * around + 1)


def get_distance(df, point, other_point):
    return abs(df.index.get_loc(point.name) - df.index.get_loc(other_point.name))
