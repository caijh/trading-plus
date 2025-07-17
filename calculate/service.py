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
    for i in range(start, len(series) - step):
        # Get the previous, current, and next values
        idx_prev, idx_cur, idx_next = i - step, i, i + step
        prev, curr, next_ = series.iloc[idx_prev], series.iloc[idx_cur], series.iloc[
            idx_next]

        if curr != 0:
            diff = min(abs(prev - curr), abs(next_ - curr)) / curr
            if diff < 0.0002:
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
