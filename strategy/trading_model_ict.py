import numpy as np
import pandas_ta as ta

from strategy.model import TradingStrategy
from strategy.trading_model import TradingModel


class ICTTradingModel(TradingModel):
    def __init__(self,
                 lookback_bos: int = 10,
                 lookback_ob: int = 10,
                 lookahead_fvg: int = 5,
                 fvg_atr_mult: float = 0.2,
                 ob_min_body_pct: float = 0.25,
                 ob_buffer_pct: float = 0.005,
                 ):
        super().__init__('ICTTradingModel')
        self.lookback_bos: int = lookback_bos
        self.lookback_ob = lookback_ob
        self.lookahead_fvg = lookahead_fvg
        self.ob_min_body_pct = ob_min_body_pct
        self.fvg_atr_mult = fvg_atr_mult
        self.ob_buffer_pct = ob_buffer_pct

    def find_recent_bos(self, df):
        """
        在最近 lookback_bos 根 K 中从近到远找 BOS（结构突破 + 收盘确认）。
        返回 (found:bool, bos_idx:int, bos_dir:'UP'|'DOWN', prev_swing_pos:int_or_None)
        依赖 df['turning'] 提供 swing positions (-1 swing high, 1 swing low)
        """
        n = len(df)
        if n < 10:
            return False, None, None, None

        turning_arr = df['turning'].values
        start = max(3, n - self.lookback_bos)
        # 从最近往前找
        for i in range(n - 2, start - 1, -1):
            close_i = df['close'].iloc[i]
            open_i = df['open'].iloc[i]
            prev_close_i = df['close'].iloc[i - 1]
            # find previous swing high/low before i
            prev_high_idxes = np.where((turning_arr == -1) & (np.arange(n) < i))[0]
            prev_low_idxes = np.where((turning_arr == 1) & (np.arange(n) < i))[0]
            prev_high_pos = prev_high_idxes[-1] if len(prev_high_idxes) > 0 else None
            prev_low_pos = prev_low_idxes[-1] if len(prev_low_idxes) > 0 else None

            # UP BOS: close > prev swing high and bullish candle
            if prev_high_pos is not None and prev_close_i < df['high'].iloc[
                prev_high_pos] < close_i and close_i > open_i:
                return True, i, 'UP', prev_high_pos

            # DOWN BOS: close < prev swing low and bearish candle
            if prev_low_pos is not None and close_i < df['low'].iloc[prev_low_pos] < prev_close_i and close_i < open_i:
                return True, i, 'DOWN', prev_low_pos

        return False, None, None, None

    def identify_strict_ob_before_bos(self, df, bos_idx, bos_dir):
        """
        更严格的 OB 识别：OB 必须是 BOS 之前最近的一根 opposite-direction candle，
        且在 lookback_ob 根内；且实体大小需 >= ob_min_body_pct * true_range。
        返回 (ob_type, ob_idx, ob_zone_low, ob_zone_high) 或 (None, None, None, None)
        """
        if bos_idx is None or bos_idx <= 0:
            return None, None, None, None

        scan_start = max(0, bos_idx - self.lookback_ob)
        # search from bos_idx-1 backward to scan_start for the nearest opposite-direction candle
        for j in range(bos_idx - 1, scan_start - 1, -1):
            o = df['open'].iloc[j]
            c = df['close'].iloc[j]
            high = df['high'].iloc[j]
            low = df['low'].iloc[j]
            body = abs(c - o)
            true_range = max(high - low, 1e-9)
            if (body / true_range) < self.ob_min_body_pct:
                continue  # too small body -> noise

            ob_zone_low = low
            ob_zone_high = high
            if bos_dir == 'UP' and c < o:
                # bullish OB (we'll call it BULL_OB because BOS was up and OB is bearish candle)
                return 'BULL_OB', j, ob_zone_low, ob_zone_high

            if bos_dir == 'DOWN' and c > o:
                return 'BEAR_OB', j, ob_zone_low, ob_zone_high

        return None, None, None, None

    def find_fvg_after_bos(self, df, bos_idx):
        """
        在 BOS 之后的窗口内寻找第一个有效 FVG（left=i, mid=i+1, right=i+2，right vs left）
        只搜索 bos_idx+1 .. bos_idx+lookahead_fvg（确保 i+2 不越界）
        返回 (fvg_type('BULL'|'BEAR'), left_idx, right_idx, left_high, left_low, right_high, right_low)
        或 (None, None, None, None, None, None, None)
        """
        n = len(df)
        if bos_idx is None:
            return None, None, None, None, None, None, None

        start = bos_idx + 1
        end = min(n - 2, bos_idx + 1 + self.lookahead_fvg)
        for i in range(start, end):
            left_high = df['high'].iloc[i]
            left_low = df['low'].iloc[i]
            right_high = df['high'].iloc[i + 2]
            right_low = df['low'].iloc[i + 2]
            atr_here = df['atr'].iloc[i + 1] if 'atr' in df.columns else \
                ta.atr(df['high'], df['low'], df['close'], length=14).iloc[i + 1]

            # Bullish FVG: right.low > left.high
            if (right_low > left_high) and ((right_low - left_high) > self.fvg_atr_mult * atr_here):
                # ensure not swallowed by subsequent bars between i and i+2 (right_low still > left_high)
                if right_low > left_high:
                    return 'BULL', i, i + 2, left_high, left_low, right_high, right_low

            # Bearish FVG: right.high < left.low
            if (right_high < left_low) and ((left_low - right_high) > self.fvg_atr_mult * atr_here):
                if right_high < left_low:
                    return 'BEAR', i, i + 2, left_high, left_low, right_high, right_low

        return None, None, None, None, None, None, None

    @staticmethod
    def check_entry_touch_and_confirm(df, ob_info, fvg_info, last_idx, prefer='OB'):
        """
        检查是否有回填并确认：
        - ob_info: (ob_type, ob_idx, ob_low, ob_high)
        - fvg_info: (fvg_type, left_idx, right_idx, left_high, left_low, right_high, right_low)
        prefer: 'OB'|'FVG'|'ANY' -> 优先用哪个触发进场（当两者同时触发）
        返回 1, -1, 或 0
        """
        cur_open = df['open'].iloc[last_idx]
        cur_close = df['close'].iloc[last_idx]
        cur_high = df['high'].iloc[last_idx]
        cur_low = df['low'].iloc[last_idx]

        # Helper to test touch (any overlap with zone)
        def touched_zone(low, high):
            midpoint = (low + high) / 2

            touch_condition = (cur_low <= midpoint) and (cur_low >= low)

            # 收盘必须突破 zone 上界
            close_condition = cur_close >= high

            return touch_condition and close_condition

        ob_type, ob_idx, ob_low, ob_high = ob_info
        # OB preferred
        if prefer in ('OB', 'ANY') and ob_type is not None:
            if ob_type == 'BULL_OB':
                touched = touched_zone(ob_low, ob_high)
                if touched and cur_close > cur_open:
                    return 1
            if ob_type == 'BEAR_OB':
                touched = touched_zone(ob_low, ob_high)
                if touched and cur_close < cur_open:
                    return -1

        # FVG fallback / alternative
        if prefer in ('FVG', 'ANY') and fvg_info is not None:
            fvg_type = fvg_info[0]
            if fvg_type == 'BULL':
                # gap interval = [left_high, right_low]
                gap_low = fvg_info[3]  # left_high
                gap_high = fvg_info[6]  # right_low
                if touched_zone(gap_low, gap_high) and cur_close > cur_open:
                    return 1
            if fvg_type == 'BEAR':
                gap_low = fvg_info[5]  # right_high
                gap_high = fvg_info[4]  # left_low
                if touched_zone(gap_low, gap_high) and cur_close < cur_open:
                    return -1

        return 0

    def get_trading_signal(self, stock, df, trending, direction):
        """
        优化版 ICT 策略：
        - 趋势过滤 (EMA)
        - 有效 FVG (需大于 ATR*0.2)
        - MSS + 回测确认
        """

        if len(df) < 200:  # 需要足够数据来计算EMA/ATR
            return 0

        # 1️⃣ 趋势过滤
        trend_up = True if stock['trending'] == 'UP' else False
        trend_down = True if stock['trending'] == 'DOWN' else False

        # 2️⃣ ATR 波动率，用于FVG过滤
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)

        # 3️⃣ MSS（市场结构转变）检测，改用 turning
        # 最近一次突破
        bos_found, bos_idx, bos_dir, prev_swing_pos = self.find_recent_bos(df)
        # print(f"BOS found: {bos_found}, idx: {bos_idx}, dir: {bos_dir}, prev_swing_pos: {prev_swing_pos}")
        # print(f'bos index date: {df.iloc[bos_idx].name.strftime('%Y-%m-%d')}')
        if not bos_found:
            return 0

        ob_type, ob_idx, ob_low, ob_high = self.identify_strict_ob_before_bos(df, bos_idx, bos_dir)
        # print(f"OB found: {ob_type}, idx: {ob_idx}, low: {ob_low}, high: {ob_high}")
        # print(f'ob index date: {df.iloc[ob_idx].name.strftime("%Y-%m-%d")}')
        if ob_type is None:
            return 0

        swallowed = False
        for k in range(ob_idx + 1, len(df)):
            if (df['low'].iloc[k] < ob_low) and (df['high'].iloc[k] > ob_high):
                swallowed = True
                break
        if swallowed:
            return 0

        fvg_info = self.find_fvg_after_bos(df, bos_idx)
        # print(f"FVG found: {fvg_info}")
        entry_signal = self.check_entry_touch_and_confirm(
            df,
            (ob_type, ob_idx, ob_low, ob_high),
            fvg_info,
            len(df) - 1,
            prefer='ANY'
        )
        # 5️⃣ 交易逻辑：必须符合趋势 + FVG + MSS
        # 📈 多头信号
        if entry_signal == 1 and trend_up:
            return 1
        # 📉 空头信号
        if entry_signal == -1 and trend_down:
            return 0
        return entry_signal

    def create_trading_strategy(self, stock, df, signal):
        """
        策略优化：
        - 入场价 = 当前收盘价
        - 止损 = 最近 swing high/low (来自 turning)
        - 止盈 = RR = 2:1
        """
        # re-identify BOS & OB to get positions/values (could cache to avoid double compute)
        bos_found, bos_idx, bos_dir, prev_swing_pos = self.find_recent_bos(df)
        ob_type, ob_idx, ob_low, ob_high = self.identify_strict_ob_before_bos(df, bos_idx, bos_dir)

        last_close = float(df['close'].iloc[-1])
        n_digits = 3 if stock.get('stock_type') == 'Fund' else 2
        swing_highs = df[df['turning'] == -1]
        swing_lows = df[df['turning'] == 1]
        if signal == 1:
            if ob_low is None:
                return None
            stop_loss = float(ob_low) * (1.0 - self.ob_buffer_pct)
            entry_price = last_close * 0.995
            risk = entry_price - stop_loss
            if risk <= 0:
                return None
            target_high = swing_highs['high'].iloc[-1] if len(swing_highs) >= 1 else None
            take_profit = float(target_high) if (target_high and target_high > entry_price) else entry_price + 2 * risk

        elif signal == -1:
            if ob_high is None:
                return None
            stop_loss = float(ob_high) * (1.0 + self.ob_buffer_pct)
            entry_price = last_close * 1.005
            risk = stop_loss - entry_price
            if risk <= 0:
                return None
            target_low = swing_lows['low'].iloc[-1] if len(swing_lows) >= 1 else None
            take_profit = float(target_low) if (target_low and target_low < entry_price) else entry_price - 2 * risk

        else:
            return None

        strategy = TradingStrategy(
            strategy_name=self.name,
            stock_code=stock['code'],
            stock_name=stock['name'],
            entry_patterns=['ICT', 'MSS', 'OB', 'FVG'],
            exit_patterns=[],
            exchange=stock['exchange'],
            entry_price=float(round(entry_price, n_digits)),
            take_profit=float(round(take_profit, n_digits)),
            stop_loss=float(round(stop_loss, n_digits)),
            signal=signal
        )
        return strategy

