import numpy as np
import pandas_ta as ta

from analysis.model import AnalyzedStock
from dataset.service import create_dataframe
from extensions import db
from indicator.service import get_patterns, get_volume_patterns, get_match_patterns
from stock.service import KType, get_stock_prices


def save_analyzed_stocks(stocks):
    """
    将分析过的股票数据插入数据库中。此函数首先根据股票代码删除已存在的股票数据，
    然后将新的股票数据插入到AnalyzedStock表中。

    参数:
    stocks (list): 包含股票数据的列表，每个股票数据是一个字典，包含股票的代码、名称
                   和其他分析数据如模式、支撑位和阻力位。
    """

    if len(stocks) == 0:
        return

    # 把分析过股票插入数据中，根据code删除原有的，再插入AnalyzedStock对应的表中
    with db.session.begin():
        for stock in stocks:
            try:
                save_analyzed_stock(stock)
            except Exception as e:
                print(f"处理 stock 出错: {stock['code']}, 错误信息: {e}")
        db.session.commit()


def save_analyzed_stock(stock):
    analyzed_stock = AnalyzedStock(
        code=stock["code"],
        name=stock["name"],
        exchange=stock["exchange"],
        patterns=stock.get("patterns", []),
        support=stock.get("support"),
        resistance=stock.get("resistance"),
        price=stock.get("price", None)
    )
    db.session.add(analyzed_stock)
    print(f"Add {analyzed_stock} to AnalyzedStock")


def analyze_stock(stock, k_type=KType.DAY, signal=1):
    print("=====================================================")
    code = stock['code']
    name = stock['name']
    stock['patterns'] = []
    prices = get_stock_prices(code, k_type)
    if not prices:
        print(f'No prices get for  stock {code}')
        return stock
    else:
        print(f'Analyzing Stock, code = {code}, name = {name}')
        candlestick_patterns, ma_patterns = get_patterns(signal)

        df = create_dataframe(stock, prices)

        matched_candlestick_patterns, candlestick_weight = get_match_patterns(candlestick_patterns, stock, prices,
                                                                              df)
        if signal == 1:
            min_candlestick_weight = 0
            if candlestick_weight > min_candlestick_weight:
                matched_ma_patterns, ma_weight = get_match_patterns(ma_patterns, stock, prices, df)
                volume_patterns = get_volume_patterns(matched_ma_patterns)
                matched_volume_patterns, volume_weight = get_match_patterns(volume_patterns, stock, prices, df)
                if ma_weight > 1 and volume_weight > 1:
                    # 将所有匹配的K线形态、均线和量能模式的标签添加到股票的模式列表中
                    append_matched_pattern_label(matched_candlestick_patterns, stock)
                    append_matched_pattern_label(matched_ma_patterns, stock)
                    append_matched_pattern_label(matched_volume_patterns, stock)
        else:
            matched_ma_patterns, ma_weight = get_match_patterns(ma_patterns, stock, prices, df)
            volume_patterns = get_volume_patterns(matched_ma_patterns)
            matched_volume_patterns, volume_weight = get_match_patterns(volume_patterns, stock, prices, df)
            if ma_weight > 1 and volume_weight > 0:
                # 同样将所有匹配的模式标签添加到股票的模式列表中
                append_matched_pattern_label(matched_candlestick_patterns, stock)
                append_matched_pattern_label(matched_ma_patterns, stock)
                append_matched_pattern_label(matched_volume_patterns, stock)

        # 计算给定股票的支持位和阻力位
        # 参数:
        #   stock: 包含股票数据的字典或数据框，应包括历史价格等信息
        #   df: 用于计算支持位和阻力位的数据框，通常包含历史价格数据
        # 返回值:
        #   support: 计算得到的支持位价格
        #   resistance: 计算得到的阻力位价格
        (support, resistance) = calculate_support_resistance(stock, df)
        (support_n, resistance_n) = calculate_support_resistance_by_turning_points(stock, df)
        if support_n is not None:
            support = support_n
        if resistance_n is not None:
            resistance = resistance_n

        # latest_volume = df.iloc[-1]['volume']
        # if latest_volume > 0:
        #     (support_vwap, resistance_vwap) = calculate_vwap_support_resistance(stock, df, window=5)
        #     if support_vwap < support:
        #         support = support_vwap
        #     if resistance_vwap < resistance:
        #         resistance = resistance_vwap

        # 将计算得到的支持位和阻力位添加到股票数据中
        stock['support'] = support
        stock['resistance'] = resistance
        stock['price'] = float(prices[-1]['close'])

    print(
        f'Analyzing Complete code = {code}, name = {name}, patterns = {stock["patterns"]}, support = {stock["support"]}, resistance = {stock["resistance"]}')

    return stock


def append_matched_pattern_label(matched_patterns, stock):
    """
    将匹配到的模式标签添加到股票信息中。

    遍历匹配到的模式列表，将每个模式的标签添加到指定的股票信息字典中的 'patterns' 键下。

    参数:
    matched_patterns: 匹配到的模式对象列表，每个模式对象包含一个 'label' 属性，用于表示模式的标签。
    stock: 包含股票信息的字典，必须包含一个 'patterns' 键，用于存储模式标签的列表。

    返回:
    无返回值。此函数直接修改传入的股票信息字典。
    """
    # 遍历匹配到的模式列表
    for matched_pattern in matched_patterns:
        # 将模式的标签添加到股票信息的 'patterns' 列表中
        stock['patterns'].append(matched_pattern.label)


def calculate_support_resistance(stock, df):
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

    # 提取最新数据行，用于计算最终的支撑位和阻力位
    latest_data = df.iloc[-1][['Pivot', 'S1', 'R1', 'S2', 'R2', 'S3', 'R3']]

    n_digits = 3 if stock['stock_type'] == 'Fund' else 2
    # 计算最终的支撑位和阻力位
    s = round(float(min(latest_data['S1'], latest_data['S2'], latest_data['S3'])), n_digits)
    r = round(float(min(latest_data['R1'], latest_data['R2'], latest_data['R3'])), n_digits)

    # 打印计算结果
    print(f'{stock["code"]} calculate_support_resistance Support = {s}, Resistance = {r}')

    return s, r


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


def detect_turning_points(series, angle_threshold_degrees=135):
    """
    Detect turning points in a given series.

    This function aims to identify the turning points in a series, which include both upward and downward turning points.
    An upward turning point is defined as a point where the value is lower than the values before and after it.
    A downward turning point is defined as a point where the value is higher than the values before and after it.

    Parameters:
    series (pd.Series): The input series, assumed to be a pandas series.

    Returns:
    tuple: A tuple containing three lists, the first list contains all turning points (upward and downward),
           the second list contains only upward turning points, and the third list contains only downward turning points.
    """
    # Initialize lists to store all turning points, upward turning points, and downward turning points
    turning_points = []
    turning_up_points = []
    turning_down_points = []
    angle_threshold_cos = np.cos(np.radians(angle_threshold_degrees))  # Convert to cosine for dot product check

    # Iterate through the series, excluding the first and last elements, as they cannot form a turning point by definition
    for i in range(1, len(series) - 1):
        # Get the previous, current, and next values
        idx_prev, idx_cur, idx_next = i - 1, i, i + 1
        prev, curr, next_ = series.iloc[idx_prev], series.iloc[idx_cur], series.iloc[idx_next]

        # Vectors: v1 = P1->P2, v2 = P3->P2 (note the direction toward middle point)
        v1 = np.array([idx_cur - idx_prev, curr - prev])
        v2 = np.array([idx_next - idx_cur, next_ - curr])

        v1_norm = np.linalg.norm(v1)
        v2_norm = np.linalg.norm(v2)

        if v1_norm == 0 or v2_norm == 0:
            continue

        cos_theta = np.dot(v1, v2) / (v1_norm * v2_norm)

        if cos_theta > angle_threshold_cos:
            continue

        # Determine if the current point is an upward turning point
        if prev > curr and curr < next_:
            turning_up_points.append(i)
            turning_points.append(i)

        # Determine if the current point is a downward turning point
        if prev < curr and curr > next_:
            turning_down_points.append(i)
            turning_points.append(i)

    # Return all turning points and the respective upward and downward turning points
    return turning_points, turning_up_points, turning_down_points


def select_score_point(stock, df, points, current_price, is_support=True):
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
    recent_points['score'] = recent_points.index.map(lambda idx: score_turning_point(df, idx, current_price)['score'])
    point = recent_points.sort_values('score', ascending=False).iloc[0]
    print(point)
    return cal_price_from_kline(stock, df, point, current_price, is_support)


def select_nearest_point(stock, df, points, current_price, is_support=True, recent_num=2):
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
    recent_points['dist'] = (recent_points['ma'] - current_price).abs()
    point = recent_points.sort_values('dist').iloc[0]
    print(point)
    return cal_price_from_kline(stock, df, point, current_price, is_support)


def cal_price_from_kline(stock, df, point, current_price, is_support):
    kline = df.loc[point.name]
    price = kline['high'] if is_support else kline['low']
    # 防止支撑价高于当前价 / 阻力价低于当前价
    if is_support and price > current_price:
        price = kline['low']
        if price > current_price:
            price = kline['ma']
    elif not is_support and price < current_price:
        price = kline['high']
        if price < current_price:
            price = kline['ma']

    formatted_date = point.name.strftime('%Y-%m-%d %H:%M:%S')
    if is_support:
        stock['support_date'] = formatted_date
    else:
        stock['resistance_date'] = formatted_date

    return price


def score_turning_point(
    df,
    point_index,
    current_price,
    window=5,
    slope_window=3,
    price_tolerance=0.005,
    weights=None
):
    """
    计算给定点的转折点得分。

    参数:
    - df: 包含价格和成交量等数据的DataFrame。
    - point_index: 需要计算得分的转折点索引。
    - current_price: 当前价格。
    - window: 计算得分时考虑的数据窗口大小，默认为5。
    - slope_window: 计算斜率时考虑的数据窗口大小，默认为3。
    - price_tolerance: 价格容忍度，用于计算触价得分，默认为0.005。
    - weights: 各个得分项的权重，默认为{"dist": 0.5, "slope": 0.2, "touch": 0.15, "volume": 0.15}。

    返回:
    - 一个字典，包含转折点得分和其他相关信息。
    """
    # 检查point_index是否在DataFrame的索引中
    if point_index not in df.index:
        return {"score": 0}

    # 设置默认的权重值
    weights = weights or {"dist": 0.5, "slope": 0.2, "touch": 0.15, "volume": 0.15}

    try:
        # 获取转折点在DataFrame中的位置索引
        idx = df.index.get_loc(point_index)
        # 确保有足够的数据点来计算得分
        if idx < window or idx + window >= len(df):
            return {"score": 0}

        # 提取移动平均价格序列和转折点的价格
        ma_series = df['ma']
        price_at_turn = ma_series.iloc[idx]

        # 计算价格的最大可能距离
        max_dist = max(abs(df['close'].max() - df['close'].min()), 1e-3)
        # 计算转折点价格与当前价格的原始距离
        raw_dist = abs(price_at_turn - current_price)
        # 计算距离得分
        dist_score = 1 - min(raw_dist / max_dist, 1)

        # 计算左右斜率
        left_slope = ma_series.iloc[idx] - ma_series.iloc[idx - slope_window]
        right_slope = ma_series.iloc[idx + slope_window] - ma_series.iloc[idx]
        # 计算斜率得分
        slope_score = abs(left_slope - right_slope)
        slope_score /= max(ma_series.std(), 1e-6)
        slope_score = min(slope_score, 1.0)

        # 计算触价得分
        tolerance_range = price_at_turn * price_tolerance
        touch_count = df[
            (df['close'] >= price_at_turn - tolerance_range) &
            (df['close'] <= price_at_turn + tolerance_range)
        ].shape[0]
        touch_score = touch_count / len(df)

        # 计算成交量得分
        local_volume = df['volume'].iloc[idx - window: idx + window + 1].mean()
        avg_volume = df['volume'].mean()
        volume_score = min(local_volume / max(avg_volume, 1e-6), 1.0)

        # 综合各项得分计算最终得分
        score = (
            weights["dist"] * dist_score +
            weights["slope"] * slope_score +
            weights["touch"] * touch_score +
            weights["volume"] * volume_score
        )

        # 返回包含各项得分和转折点信息的字典
        return {
            "score": round(score, 4),
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
    recent_df['ma'] = ta.ema(recent_df['close'], window)

    # 找出均线的拐点位置
    turning_points_idxes, turning_up_idxes, turning_down_idxes = detect_turning_points(recent_df['ma'])

    # 提取拐点价格及索引
    turning_points = recent_df.iloc[turning_points_idxes][['ma', 'close']]
    turning_up_points = recent_df.iloc[turning_up_idxes][['ma', 'close']]
    turning_down_points = recent_df.iloc[turning_down_idxes][['ma', 'close']]

    # 获取当前价格、最近的向上拐点和向下拐点
    current_price = recent_df['close'].iloc[-1]
    nearest_up_index = turning_up_idxes[-1]
    nearest_down_index = turning_down_idxes[-1]
    # 判断当前趋势
    upping = True if nearest_up_index > nearest_down_index else False
    stock['direction'] = 'UP' if upping else 'DOWN'

    # 支撑点：拐点价格 < 当前价格
    supports = turning_down_points[turning_down_points['ma'] < current_price]
    resistances = turning_up_points[turning_up_points['ma'] > current_price]

    # 找最靠近当前价格的支撑和阻力（按时间最近，取所在K线的低 / 高点）
    support = None
    resistance = None
    if upping:
        first_point = turning_points.iloc[-1]
        second_point = turning_points.iloc[-2]
        print("Support point:")
        if current_price > second_point['ma']:
            print(second_point)
            support = cal_price_from_kline(stock, recent_df, second_point, current_price, is_support=True)
        else:
            print(first_point)
            support = cal_price_from_kline(stock, recent_df, first_point, current_price, is_support=True)

        if not resistances.empty and resistance is None:
            print("Resistance point:")
            resistance = select_score_point(stock, recent_df, resistances, current_price, is_support=False)
    else:
        if not supports.empty and support is None:
            print("Support point:")
            support = select_nearest_point(stock, recent_df, supports, current_price, is_support=True)  # 时间上最靠近当前的支撑点

        first_point = turning_points.iloc[-1]
        second_point = turning_points.iloc[-2]
        print("Resistance point:")
        if current_price < second_point['ma']:
            print(second_point)
            resistance = cal_price_from_kline(stock, recent_df, second_point, current_price, is_support=False)
        else:
            print(first_point)
            resistance = cal_price_from_kline(stock, recent_df, first_point, current_price, is_support=False)

    # 根据基金或股票类型决定小数点保留位数
    n_digits = 3 if stock.get('stock_type') == 'Fund' else 2
    s = round(float(support), n_digits) if support else None
    r = round(float(resistance), n_digits) if resistance else None

    # 打印计算结果
    print(
        f'{stock["code"]} calculate_support_resistance_by_turning_points Support = {s}, Resistance = {r}, Price = {current_price}')
    return s, r
