import statistics

import numpy as np
import pandas_ta as ta

from stock.constant import Direction, Trend


def get_recent_extreme_idx(df, index, price_type, recent=2):
    """
    在指定 index 附近窗口内找到极值索引（最高或最低）。
    """
    start_idx = max(0, index - recent)
    end_idx = min(len(df), index + recent + 1)
    window_slice = df.iloc[start_idx:end_idx]

    if price_type == "low":
        return window_slice["low"].idxmin()
    elif price_type == "high":
        return window_slice["high"].idxmax()
    return None


def group_and_refine(points, df, price_type, merge_window=4, recent=3):
    """
    将相邻的拐点按窗口分组，并精炼为真正的极值点。

    Args:
        points (list[int]): 初步检测的拐点索引。
        df (pd.DataFrame): K线数据。
        price_type (str): 'low' or 'high'。
        merge_window (int): 分组合并的最大间隔。
        recent (int): 搜索极值的窗口范围。

    Returns:
        list[int]: 精炼后的极值点索引。
    """
    if not points:
        return []

    groups = [[points[0]]]
    for i in range(1, len(points)):
        if points[i] - points[i - 1] <= merge_window:
            groups[-1].append(points[i])
        else:
            groups.append([points[i]])

    refined = []
    for g in groups:
        last_idx = None
        for e in g:
            idx = get_recent_extreme_idx(df, e, price_type, recent)
            if last_idx is None:
                last_idx = idx
            else:
                if price_type == 'low':
                    if df.loc[idx]['low'] < df.loc[last_idx]['low']:
                        last_idx = idx
                if price_type == 'high':
                    if df.loc[idx]['high'] > df.loc[last_idx]['high']:
                        last_idx = idx
        refined.append(last_idx)
    return refined


def detect_turning_point_indexes(series, df=None, merge_window=4):
    """
    检测时间序列的转折点（局部高/低点），并支持用 K 线数据精炼。

    Args:
        series (pd.Series): 输入序列。
        df (pd.DataFrame, optional): K线数据，包含 'high' 和 'low'。
        merge_window (int): 分组合并窗口。

    Returns:
        tuple: (all_points, up_points, down_points)
    """
    prev, next_ = series.shift(1), series.shift(-1)

    # 初步转折点
    up_points = series[(prev > series) & (series < next_)].index.tolist()
    down_points = series[(prev < series) & (series > next_)].index.tolist()

    # 精炼
    if df is not None:
        up_points = group_and_refine(up_points, df, "low", merge_window, recent=3)
        down_points = group_and_refine(down_points, df, "high", merge_window, recent=3)

    all_points = sorted(set(up_points + down_points))

    # 初始化最终输出列表及状态变量
    all_point_idxes = []
    up_point_idxes = []
    down_point_idxes = []
    prev_point_type = None
    prev_point = None
    # 遍历所有转折点索引，根据类型交替保留有效转折点以避免连续同向点
    for point in all_points:
        cur_point_type = 1 if point in up_points else -1
        if prev_point_type is None:
            all_point_idxes.append(point)
            if cur_point_type == 1:
                up_point_idxes.append(point)
            if cur_point_type == -1:
                down_point_idxes.append(point)
            prev_point_type = cur_point_type
            prev_point = point
        else:
            if prev_point_type == 1:
                if cur_point_type != prev_point_type:
                    all_point_idxes.append(point)
                    down_point_idxes.append(point)
                    prev_point_type = cur_point_type
                    prev_point = point
                else:
                    replace_prev = False
                    if df is not None:
                        if df.loc[point]['low'] < df.loc[prev_point]['low']:
                            replace_prev = True
                    else:
                        if series.loc[point] < series.loc[prev_point]:
                            replace_prev = True
                    if replace_prev:
                        all_point_idxes.remove(prev_point)
                        all_point_idxes.append(point)
                        up_point_idxes.remove(prev_point)
                        up_point_idxes.append(point)
                        prev_point_type = cur_point_type
                        prev_point = point
            if prev_point_type == -1:
                if cur_point_type != prev_point_type:
                    all_point_idxes.append(point)
                    up_point_idxes.append(point)
                    prev_point_type = cur_point_type
                    prev_point = point
                else:
                    replace_prev = False
                    if df is not None:
                        if df.loc[point]['high'] > df.loc[prev_point]['high']:
                            replace_prev = True
                    else:
                        if series.loc[point] > series.loc[prev_point]:
                            replace_prev = True
                    if replace_prev:
                        all_point_idxes.remove(prev_point)
                        all_point_idxes.append(point)
                        down_point_idxes.remove(prev_point)
                        down_point_idxes.append(point)
                        prev_point_type = cur_point_type
                        prev_point = point

    return all_point_idxes, up_point_idxes, down_point_idxes


def get_round_price(stock, price):
    if price is None:
        return None
    n_digits = 3 if stock.get('stock_type') == 'Fund' else 2
    return round(float(price), n_digits)


def detect_turning_points(series):
    turning_point_idxes, turning_up_point_idxes, turning_down_point_idxes = detect_turning_point_indexes(series)
    turning_points = series.loc[turning_point_idxes]
    turning_up_points = series.loc[turning_up_point_idxes]
    turning_down_points = series.loc[turning_down_point_idxes]
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
    s = round(float(statistics.mean([latest_data['S1'], latest_data['S2'], latest_data['S3']])), n_digits)
    r = round(float(statistics.mean([latest_data['R1'], latest_data['R2'], latest_data['R3']])), n_digits)
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
    turning_idxes = df.index[df['turning'] != 0]
    turning_up_idxes = df.index[df['turning'] == 1]
    turning_down_idxes = df.index[df['turning'] == -1]

    # 获取拐点对应的价格
    turning_points = df.loc[turning_idxes][['close', 'low', 'high', 'open', 'turning']]
    turning_up_points = df.loc[turning_up_idxes][['close', 'low', 'high', 'open', 'turning']]
    turning_down_points = df.loc[turning_down_idxes][['close', 'low', 'high', 'open', 'turning']]

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

    # 最近n个turning_points，保存至stock['turning']
    n = 9
    latest_turning = [
        {
            "time": row.name.strftime("%Y-%m-%d %H:%M:%S"),
            "type": 1 if row["turning"] == 1 else -1,
        }
        for _, row in turning_points.tail(min(n, len(turning_points))).iterrows()
    ]
    stock["turning"] = latest_turning

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

    if not supports.empty and support is None:
        support = select_nearest_point(stock, recent_df, supports, current_price,
                                       field=ma_name,
                                       is_support=True, recent_num=30)  # 时间上最靠近当前的支撑点
    # else:
    #     support = cal_price_from_ma(stock, recent_df, current_price, is_support=True)

    if not resistances.empty and resistance is None:
        resistance = select_score_point(stock, recent_df, resistances, current_price,
                                        ma_name,
                                        is_support=False)
    # else:
    #     resistance = cal_price_from_ma(stock, recent_df, current_price, is_support=False)

    # 如果当前处于上涨趋势，并且存在转折点数据
    # if upping and len(turning_points) > 0:
    #     # 获取最近的两个转折点，用于判断支撑位和阻力位
    #     first_point = turning_points.iloc[-1]
    #     second_point = turning_points.iloc[-2] if len(turning_points) > 1 else None
    #     support_price = None
    #
    #     # 根据当前价格与均线的关系，计算可能的支撑价格
    #     if second_point is not None and current_price > second_point[f'{ma_name}']:
    #         support_price = cal_price_from_kline(stock, recent_df, second_point, current_price, ma_name,
    #                                              is_support=True)
    #     elif current_price > first_point[f'{ma_name}']:
    #         support_price = cal_price_from_kline(stock, recent_df, first_point, current_price, ma_name, is_support=True)
    #
    #     # 如果计算出有效的支撑价格，则更新支撑位
    #     if support_price is not None:
    #         support = support_price
    #
    #     # 如果存在阻力位数据且当前未设置阻力位，则选择最近的阻力点
    #     if not resistances.empty and resistance is None:
    #         resistance_latest = select_nearest_point(stock, recent_df, resistances, current_price, ma_name,
    #                                                  is_support=False)
    #         resistance_score = select_score_point(stock, recent_df, resistances, current_price, ma_name,
    #                                               is_support=False)
    #         # 选取更接近当前价格的阻力位
    #         resistance_price = resistance_score if resistance_score < resistance_latest else resistance_latest
    #
    #         # 如果找到有效的阻力价格，则更新阻力位
    #         if resistance_price is not None:
    #             resistance = resistance_price
    #
    # # 如果不是上涨趋势，但存在转折点数据
    # elif len(turning_points) > 0:
    #     # 如果存在支撑位数据且当前未设置支撑位，则选择最近的支撑点
    #     if not supports.empty and support is None:
    #         support_price = select_nearest_point(stock, recent_df, supports, current_price, ma_name,
    #                                              is_support=True)
    #         if support_price is not None:
    #             support = support_price
    #
    #     # 获取最近的两个转折点，用于判断阻力位
    #     first_point = turning_points.iloc[-1]
    #     second_point = turning_points.iloc[-2] if len(turning_points) > 1 else None
    #     resistance_price = None
    #
    #     # 根据当前价格与均线的关系，计算可能的阻力价格
    #     if second_point is not None and current_price < second_point[f'{ma_name}']:
    #         resistance_price = cal_price_from_kline(stock, recent_df, second_point, current_price, ma_name,
    #                                                 is_support=False)
    #     elif current_price < first_point[f'{ma_name}']:
    #         resistance_price = cal_price_from_kline(stock, recent_df, first_point, current_price, ma_name,
    #                                                 is_support=False)
    #
    #     # 如果计算出有效的阻力价格，则更新阻力位
    #     if resistance_price is not None:
    #         resistance = resistance_price

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


def get_recent_price_base_index(df, index, price_type, recent=2):
    """
    在给定索引前后2个位置（共5个）的K线数据中，
    找出最高价或最低价。

    Args:
        df (pd.DataFrame): 包含 'high' 和 'low' 列的股票数据DataFrame。
        index (int): 目标K线的索引。
        price_type (str): 'high' 或 'low'，指定要查找的价格类型。
        recent: recent.

    Returns:
        float: 指定范围内的最高价或最低价。
    """
    # 确定要切片的范围，确保不超出DataFrame边界
    start_idx = max(0, index - recent)
    end_idx = min(len(df), index + recent + 1)

    # 切片获取子DataFrame
    recent_df = df.iloc[start_idx:end_idx]

    return _get_recent_price(recent_df, price_type)


def get_recent_price_base_idx(df, index, price_type, recent=2):
    """
    在给定索引前后2个位置（共5个）的K线数据中，
    找出最高价或最低价。

    Args:
        df (pd.DataFrame): 包含 'high' 和 'low' 列的股票数据DataFrame。
        index (int): 目标K线的索引。
        price_type (str): 'high' 或 'low'，指定要查找的价格类型。
        recent(int): 最近

    Returns:
        float: 指定范围内的最高价或最低价。
    """
    # 确定要切片的范围，确保不超出DataFrame边界
    start_idx = max(0, index - recent)
    end_idx = min(len(df), index + recent + 1)

    idx = start_idx
    if price_type == 'low':
        for i in range(start_idx + 1, end_idx):
            if df.iloc[i]['low'] < df.iloc[idx]['low']:
                idx = i
    elif price_type == 'high':
        for i in range(start_idx + 1, end_idx):
            if df.iloc[i]['high'] > df.iloc[idx]['high']:
                idx = i
    price = df.iloc[idx]['close']
    return idx, price


def get_total_volume_around(df, index, around=3):
    """
    计算指定索引位置前后一定范围内的成交量总和

    参数:
        df: 包含交易数据的DataFrame，必须包含 'volume' 列
        index: 作为中心位置的索引值
        around: 范围参数，表示向前和向后扩展的行数，默认为3

    返回值:
        float: 指定范围内所有成交量的总和
    """
    # 获取指定索引在DataFrame中的位置
    idx = df.index.get_loc(index)

    # 计算指定范围内的成交量总和，确保起始位置不小于0，结束位置不超过数据长度
    start_idx = max(0, idx - around)
    end_idx = min(len(df), idx + around + 1)  # +1 因为切片是左闭右开区间
    volume_total = df['volume'].iloc[start_idx:end_idx].sum()

    return volume_total


def get_avg_volume_around(df, index, around=3):
    if around == 0:
        around = 3
    total_volume = get_total_volume_around(df, index, around)
    return total_volume / (2 * around + 1)


def get_distance(df, point, other_point):
    """
    计算两个点在DataFrame索引中的位置距离

    参数:
        df (pandas.DataFrame): 包含索引的DataFrame对象
        point (object): 第一个点对象，需要有name属性
        other_point (object): 第二个点对象，需要有name属性

    返回:
        int: 两个点在DataFrame索引中的位置差的绝对值
    """
    # 获取两个点在DataFrame索引中的位置差的绝对值
    return abs(df.index.get_loc(point.name) - df.index.get_loc(other_point.name))


def get_lower_shadow(point):
    """
    计算K线图中某个交易点的下影线长度

    参数:
        point (dict): 包含交易数据的字典，必须包含 'close' 、'open'、'low' 三个键
                     'close': 收盘价
                     'open': 开盘价
                     'low': 最低价

    返回值:
        float: 下影线的长度
    """
    # 根据K线类型（阳线或阴线）计算下影线长度
    if point['close'] >= point['open']:
        # 阳线：下影线 = 开盘价 - 最低价
        return point['open'] - point['low']
    else:
        # 阴线：下影线 = 收盘价 - 最低价
        return point['close'] - point['low']


def get_upper_shadow(point):
    """
    计算K线图中某个交易点的上影线长度

    参数:
        point (dict): 包含交易数据的字典，必须包含 'close' 、'open'、'high' 三个键
                     'close': 收盘价
                     'open': 开盘价
                     'high': 最高价

    返回值:
        float: 上影线的长度
    """
    # 根据K线类型（阳线或阴线）计算上影线长度
    if point['close'] >= point['open']:
        # 阳线：上影线 = 高价 - 收盘价
        return point['high'] - point['close']
    else:
        # 阴线：上影线 = 高价 - 开盘价
        return point['high'] - point['open']



def get_price_range(point):
    return point['high'] - point['low']


def is_hammer_strict(point):
    """
    判断给定K线点是否为严格锤子线形态

    参数:
        point: K线数据点，包含开盘价、最高价、最低价、收盘价等信息

    返回值:
        bool: 如果是严格锤子线形态返回True，否则返回False
    """
    # 计算下影线长度
    lower_shadow = get_lower_shadow(point)
    # 计算K线整体波动范围
    length = get_price_range(point)

    if length == 0:
        return False

    # 判断下影线长度占整体波动范围的比例是否大于等于2/3
    return (lower_shadow / length) > (2 / 3)


def is_hangingman_strict(point):
    """
    判断给定K线点是否为严格的吊颈线形态

    吊颈线是K线图中的一种反转形态，通常出现在上涨趋势的末端，预示着可能的下跌反转。
    严格的吊颈线要求上影线长度占整个价格波动范围的比例超过0.618（黄金分割比例）。

    参数:
        point: K线数据点，包含开盘价、最高价、最低价、收盘价等信息

    返回值:
        bool: 如果是严格的吊颈线形态返回True，否则返回False
    """
    # 计算该K线的上影线长度
    up_shadow = get_upper_shadow(point)

    # 计算该K线的价格波动范围（最高价与最低价的差值）
    length = get_price_range(point)

    # 判断上影线长度占价格波动范围的比例是否超过0.618黄金分割比例
    return (up_shadow / length) > (2 / 3)


def get_amplitude(point, df):
    """
    计算指定数据点的振幅占前一个交易日收盘价的百分比

    参数:
        point: 包含当前交易日数据的Series对象，需包含 'high' 和 'low' 字段
        df: 包含历史数据的DataFrame对象，用于获取前一个交易日的收盘价

    返回值:
        float: 振幅占前一个交易日收盘价的百分比
    """
    # 计算当前交易日的振幅（最高价与最低价的差值）
    amplitude = point['high'] - point['low']

    # 获取前一个交易日的数据点
    prev_point = df.iloc[df.index.get_loc(point.name) - 1]

    # 计算振幅占前一个交易日收盘价的百分比
    amplitude_percentage = (amplitude / prev_point['close']) * 100
    return amplitude_percentage


def hammer_is_effective(point, df):
    loc = df.index.get_loc(point.name)
    # 从loc开始，如果最低价存在低于loc位置的最低价，返回false
    for i in range(loc, len(df)):
        if df.iloc[i]['low'] < point['low']:
            return False

    return True
