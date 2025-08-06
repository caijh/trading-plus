def detect_turning_points(series):
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
                if series.iloc[idx_next_next] > next_:
                    turning_up_points.append(i)
                    turning_points.append(i)
            else:
                turning_up_points.append(i)
                turning_points.append(i)

        # Determine if the current point is a downward turning point
        if prev < curr and curr > next_:
            idx_prev_prev = idx_prev - 2
            if idx_prev_prev >= 0:
                if series.iloc[idx_prev_prev] < prev:
                    turning_down_points.append(i)
                    turning_points.append(i)
            else:
                turning_down_points.append(i)
                turning_points.append(i)

    # Return all turning points and the respective upward and downward turning points
    return turning_points, turning_up_points, turning_down_points


def get_round_price(stock, price):
    if price is None:
        return None
    n_digits = 3 if stock.get('stock_type') == 'Fund' else 2
    return round(float(price), n_digits)
