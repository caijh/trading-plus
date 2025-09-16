import numpy as np
import pandas as pd
import pandas_ta as ta

from strategy.model import TradingStrategy
from strategy.trading_model import TradingModel


class ZenTradingModel(TradingModel):
    """
    更接近缠论教科书级别的工程实现（可参数化）
    主要流程：
      fractals (turning) -> pens -> lines -> zhongshu -> 信号判定
    注意：
      - 需要 df 的 index 为时间索引或任意唯一标签索引（代码用 df.index.get_loc 做位置映射）
      - 推荐调用端事先计算好 df['EMA5'] 以及 df['volume'] 等（若没有，模型会尝试计算部分指标）
    """

    def __init__(self,
                 name: str = "ZenTradingModel",
                 min_bars_between_fractals: int = 3,
                 min_pen_bars: int = 3,
                 ema_short: int = 20,
                 ema_long: int = 50,
                 pullback_window: int = 10,
                 backlash_volume_lookback: int = 20):
        super().__init__(name)
        self.min_bars_between_fractals = int(min_bars_between_fractals)
        self.min_pen_bars = int(min_pen_bars)
        self.ema_short = int(ema_short)
        self.ema_long = int(ema_long)
        self.pullback_window = int(pullback_window)
        self.backlash_volume_lookback = int(backlash_volume_lookback)

    # ---------------- 笔 ----------------
    def build_pens(self, df: pd.DataFrame, fractals: pd.Series) -> list:
        """
        从分型构造笔（工程化规则）：
          - 选取相邻异向分型对（底->顶 为上升笔，顶->底 为下降笔）
          - 两分型之间至少 min_bars_between_fractals
          - 笔的 high/low 取两端分型 high/low
          - 输出的 pen 包含 start/end label 与 start_loc/end_loc（整数位置）
        """
        pens = []
        nonzero = fractals[fractals != 0]
        idxes = nonzero.index.tolist()
        vals = nonzero.values.tolist()
        if len(idxes) < 2:
            return pens

        for i in range(len(idxes) - 1):
            t1, t2 = vals[i], vals[i + 1]
            if t1 * t2 >= 0:
                continue
            pos1, pos2 = idxes[i], idxes[i + 1]
            loc1 = df.index.get_loc(pos1)
            loc2 = df.index.get_loc(pos2)
            if abs(loc2 - loc1) < self.min_bars_between_fractals:
                continue
            high = float(max(df['high'].iloc[loc1], df['high'].iloc[loc2]))
            low = float(min(df['low'].iloc[loc1], df['low'].iloc[loc2]))
            direction = 1 if (t1 == -1 and t2 == 1) else -1
            pens.append({
                'start': pos1,
                'end': pos2,
                'start_loc': int(loc1),
                'end_loc': int(loc2),
                'high': high,
                'low': low,
                'direction': direction
            })

        # 合并非常短或噪音笔（方向相同且间隔短）
        merged = []
        for p in pens:
            if not merged:
                merged.append(p)
                continue
            prev = merged[-1]
            gap = p['start_loc'] - prev['end_loc']
            if p['direction'] == prev['direction'] and gap <= self.min_pen_bars:
                # 合并为一个笔（扩展 end）
                prev['end'] = p['end']
                prev['end_loc'] = p['end_loc']
                prev['high'] = max(prev['high'], p['high'])
                prev['low'] = min(prev['low'], p['low'])
            else:
                merged.append(p)
        return merged

    # ---------------- 线段 ----------------
    def build_lines(self, pens: list) -> list:
        """
        将笔合并为线段：
          - 当笔方向变化时，关闭当前线段并把它 append
          - 同方向笔则扩展当前线段
        每条 line 包含 start/end label 与 start_loc/end_loc、high、low、direction
        """
        if not pens:
            return []
        lines = []
        cur = {
            'start': pens[0]['start'],
            'end': pens[0]['end'],
            'start_loc': pens[0]['start_loc'],
            'end_loc': pens[0]['end_loc'],
            'high': pens[0]['high'],
            'low': pens[0]['low'],
            'direction': pens[0]['direction']
        }
        for p in pens[1:]:
            if p['direction'] != cur['direction']:
                lines.append(cur)
                cur = {
                    'start': p['start'],
                    'end': p['end'],
                    'start_loc': p['start_loc'],
                    'end_loc': p['end_loc'],
                    'high': p['high'],
                    'low': p['low'],
                    'direction': p['direction']
                }
            else:
                # 扩展当前线段
                cur['end'] = p['end']
                cur['end_loc'] = p['end_loc']
                cur['high'] = max(cur['high'], p['high'])
                cur['low'] = min(cur['low'], p['low'])
        lines.append(cur)
        return lines

    # ---------------- 中枢（基于 lines） ----------------
    def find_zone(self, lines: list) -> list:
        """
        基于线段识别中枢（严格）：
          - 初始中枢由连续三段 line 的交集构成（top = min(highs), bottom = max(lows)）
          - 向后扩展：若下一个 line 与当前中枢有交集则扩展 end_line 与 top/bottom
          - 记录 start_line, end_line, start_loc, end_loc, top, bottom
        返回：list of dict
        """
        zs_list = []
        n = len(lines)
        if n < 3:
            return zs_list

        i = 0
        while i <= n - 3:
            top = min(lines[i]['high'], lines[i + 1]['high'], lines[i + 2]['high'])
            bottom = max(lines[i]['low'], lines[i + 1]['low'], lines[i + 2]['low'])
            if bottom <= top:
                z = {
                    'start_line': i,
                    'end_line': i + 2,
                    'top': float(top),
                    'bottom': float(bottom),
                    'start_loc': lines[i].get('start_loc'),
                    'end_loc': lines[i + 2].get('end_loc')
                }
                # 向后尝试扩展
                j = i + 3
                while j < n:
                    new_top = min(z['top'], lines[j]['high'])
                    new_bottom = max(z['bottom'], lines[j]['low'])
                    if new_bottom <= new_top:
                        z['top'] = float(new_top)
                        z['bottom'] = float(new_bottom)
                        z['end_line'] = j
                        z['end_loc'] = lines[j].get('end_loc')
                        j += 1
                    else:
                        break
                zs_list.append(z)
                i = j  # 跳到扩展后的下一段
            else:
                i += 1
        return zs_list

    # ---------------- 背驰检测（量能 + MACD） ----------------
    def detect_backlash(self, df: pd.DataFrame) -> bool:
        """
        尝试量能 + MACD 背驰判断：
          - 若最近 price 创新高/新低，但量能下降并且 MACD 柱较弱，则判断为背驰
        返回 True 表示存在背驰（风险），False 表示未检测到背驰
        """
        # 简单健壮性检查
        if len(df) < max(10, self.backlash_volume_lookback):
            return False

        # 如果没有 volume，则不能做量能背驰，但我们仍可用 MACD 柱作为参考
        has_volume = 'volume' in df.columns and df['volume'].notna().sum() > 0

        # 计算 macd 柱（若未计算）
        macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
        if 'MACDh_12_26_9' in macd.columns:
            macd_hist = macd['MACDh_12_26_9']
        else:
            macd_hist = macd.iloc[:, -1] if not macd.empty else pd.Series(0, index=df.index)

        cur = df['close'].iloc[-1]
        recent = df['close'].iloc[-self.backlash_volume_lookback:]
        recent_high = recent.max()
        recent_low = recent.min()

        # 价创高但量能下降 + macd_hist 降低
        if cur >= recent_high:
            vol_decrease = False
            macd_decrease = False
            if has_volume:
                vols = df['volume'].iloc[-self.backlash_volume_lookback:]
                if len(vols) >= 10:
                    vol_decrease = vols.iloc[-5:].mean() < vols.iloc[-10:-5].mean()
            # macd 检查
            if len(macd_hist.dropna()) >= 6:
                macd_decrease = macd_hist.iloc[-3:].mean() < macd_hist.iloc[-6:-3].mean()
            # 合并判断
            if (has_volume and vol_decrease) or macd_decrease:
                return True

        # 价创低但量能下降 + macd_hist 弱化（对称）
        if cur <= recent_low:
            vol_decrease = False
            macd_decrease = False
            if has_volume:
                vols = df['volume'].iloc[-self.backlash_volume_lookback:]
                if len(vols) >= 10:
                    vol_decrease = vols.iloc[-5:].mean() < vols.iloc[-10:-5].mean()
            if len(macd_hist.dropna()) >= 6:
                macd_decrease = macd_hist.iloc[-3:].mean() < macd_hist.iloc[-6:-3].mean()
            if (has_volume and vol_decrease) or macd_decrease:
                return True

        return False

    # ---------------- 买卖点判定（核心） ----------------
    def get_trading_signal(self, stock: dict, df: pd.DataFrame, trending=None, direction=None) -> int:
        """
        主判定入口（返回 1 / -1 / 0）
        逻辑：
          - 先计算 EMA 作为趋势参考（本级别）
          - fractals -> pens -> lines -> zs
          - 若存在最近中枢（last_z）：
              * 判断中枢结束后是否发生突破（突破必须在中枢结束之后）
              * 若突破，查找突破后的回抽窗口（pullback_window），检测是否触及中枢边界（上沿/下沿）
              * 符合突破+回抽+多头趋势 -> 一类买点（返回 1）
              * 二类/三类等按中枢序列关系判断
          - 若无中枢，用笔/线段做备选顺势跟随
        返回时同时会把触发原因以 meta 字段填回（方便回测分析）
        """
        # 基本健壮性
        if len(df) < 30:
            return 0

        # 计算 ema（不改变原 df）
        ema_s = ta.ema(df['close'], length=self.ema_short)
        ema_l = ta.ema(df['close'], length=self.ema_long)
        bullish_trend = ema_s.iloc[-1] > ema_l.iloc[-1]
        bearish_trend = ema_s.iloc[-1] < ema_l.iloc[-1]

        # fractals（Series）
        fractals = df['turning']
        pens = self.build_pens(df, fractals)
        lines = self.build_lines(pens)
        zs = self.find_zone(lines)

        last_close = float(df['close'].iloc[-1])

        # helper: 安全取值
        def safe_get_last(item_list):
            return item_list[-1] if item_list else None

        last_z = safe_get_last(zs)
        last_line = safe_get_last(lines)
        last_pen = safe_get_last(pens)

        # 记录 meta 用于回测审计
        signal_meta = {
            'reason': None,
            'last_z': last_z,
            'last_line': last_line,
            'last_pen': last_pen
        }

        # --- 基于中枢的判定（首要） ---
        if last_z is not None:
            # 使用 loc 映射判断中枢结束位置
            z_top = last_z['top']
            z_bottom = last_z['bottom']
            z_end_loc = last_z.get('end_loc', None)
            if z_end_loc is None:
                # 如果没有 end_loc，则尝试用 lines 中的 end_loc fallback
                if last_line:
                    z_end_loc = last_line.get('end_loc', len(df) - 1)
                else:
                    z_end_loc = len(df) - 1

            # 中枢结束后到当前的区间
            post_start = z_end_loc + 1
            if post_start < len(df):
                post_df = df.iloc[post_start:]
            else:
                post_df = df.iloc[0:0]

            # 检查是否在中枢结束后发生突破（向上或向下）
            left_up = (not post_df.empty) and (post_df['high'].max() > z_top)
            left_down = (not post_df.empty) and (post_df['low'].min() < z_bottom)

            # 若向上离开，找到第一次向上突破的 bar 索引（相对 df）
            breakout_up_idx = None
            if left_up:
                cond_after = df[df['high'] > z_top].iloc[post_start:]
                rel = np.nonzero(cond_after.to_numpy())[0]
                if rel.size > 0:
                    breakout_up_idx = int(post_start + rel[0])

            breakout_down_idx = None
            if left_down:
                cond_after = df[df['low'] < z_bottom].iloc[post_start:]
                rel = np.nonzero(cond_after.to_numpy())[0]
                if rel.size > 0:
                    breakout_down_idx = int(post_start + rel[0])

            # Pullback 检测（突破后若干根内回抽触及中枢上/下沿）
            pullback_hit_up = False
            if breakout_up_idx is not None:
                start = breakout_up_idx + 1
                end = min(len(df), start + self.pullback_window)
                if start < end:
                    seg = df.iloc[start:end]
                    if not seg.empty and seg['low'].min() <= z_top:
                        pullback_hit_up = True

            pullback_hit_down = False
            if breakout_down_idx is not None:
                start = breakout_down_idx + 1
                end = min(len(df), start + self.pullback_window)
                if start < end:
                    seg = df.iloc[start:end]
                    if not seg.empty and seg['high'].max() >= z_bottom:
                        pullback_hit_down = True

            # 一类买点（多头）：发生离开向上 + 回抽触及上沿 + 多头趋势 + 非背驰
            if left_up and pullback_hit_up and bullish_trend:
                if not self.detect_backlash(df):
                    # 最终确认：最近 2~3 根收盘回升
                    cond_confirm = False
                    if len(df) >= 3:
                        cond_confirm = df['close'].iloc[-3] < df['close'].iloc[-2] < df['close'].iloc[-1]
                    elif len(df) >= 2:
                        cond_confirm = df['close'].iloc[-2] < df['close'].iloc[-1]
                    if cond_confirm:
                        signal_meta['reason'] = 'zhongshu_left_up_pullback_confirm'
                        self._last_signal_meta = signal_meta
                        return 1

            # 二类（持续离开但未回抽到中枢上沿），视作强势二类买点（可风险更高）
            if left_up and (not pullback_hit_up) and bullish_trend:
                # 进一步要求突破后价格保持在中枢上方若干根
                if breakout_up_idx is not None:
                    hold_len = len(df) - breakout_up_idx
                    if hold_len >= 2:
                        signal_meta['reason'] = 'zhongshu_left_up_no_pullback'
                        self._last_signal_meta = signal_meta
                        return 1

            # 三类（新中枢突破）：新中枢 top 超过前中枢 top 且突破前中枢 top
            if len(zs) >= 2:
                prev_z = zs[-2]
                if last_z['top'] > prev_z['top'] and last_close > prev_z['top'] and bullish_trend:
                    signal_meta['reason'] = 'zone_new_top_break_prev'
                    self._last_signal_meta = signal_meta
                    return 1

            # 空头对称
            if left_down and pullback_hit_down and bearish_trend:
                if not self.detect_backlash(df):
                    cond_confirm = False
                    if len(df) >= 3:
                        cond_confirm = df['close'].iloc[-3] > df['close'].iloc[-2] > df['close'].iloc[-1]
                    elif len(df) >= 2:
                        cond_confirm = df['close'].iloc[-2] > df['close'].iloc[-1]
                    if cond_confirm:
                        signal_meta['reason'] = 'zone_left_down_pullback_confirm'
                        self._last_signal_meta = signal_meta
                        return -1

            if left_down and (not pullback_hit_down) and bearish_trend:
                if breakout_down_idx is not None:
                    hold_len = len(df) - breakout_down_idx
                    if hold_len >= 2:
                        signal_meta['reason'] = 'zone_left_down_no_pullback'
                        self._last_signal_meta = signal_meta
                        return -1

            if len(zs) >= 2:
                prev_z = zs[-2]
                if last_z['bottom'] < prev_z['bottom'] and last_close < prev_z['bottom'] and bearish_trend:
                    signal_meta['reason'] = 'zone_new_bottom_break_prev'
                    self._last_signal_meta = signal_meta
                    return -1

        # --- 若无中枢，用线段 / 笔 做备选顺势跟随 ---
        if last_pen is not None:
            # 多头备选：最后一笔为上升且本级别趋势多头，并且价格回抽到笔低附近并回升
            if last_pen['direction'] == 1 and bullish_trend:
                pen_low = last_pen['low']
                # 最近 5 根最低触及笔低并且最近收盘回升
                if len(df) >= 2 and df['low'].iloc[-5:].min() <= pen_low and df['close'].iloc[-1] > df['close'].iloc[
                    -2]:
                    signal_meta['reason'] = 'pen_support_rebound'
                    self._last_signal_meta = signal_meta
                    return 1
            if last_pen['direction'] == -1 and bearish_trend:
                pen_high = last_pen['high']
                if len(df) >= 2 and df['high'].iloc[-5:].max() >= pen_high and df['close'].iloc[-1] < df['close'].iloc[
                    -2]:
                    signal_meta['reason'] = 'pen_resistance_rebound'
                    self._last_signal_meta = signal_meta
                    return -1

        # 默认无信号
        self._last_signal_meta = signal_meta
        return 0

    # ---------------- 交易策略生成（含 meta） ----------------
    def create_trading_strategy(self, stock: dict, df: pd.DataFrame, signal: int):
        """
        返回 TradingStrategy，包含 entry_price, stop_loss, take_profit 与 meta（触发理由 / zhongshu info）
        """
        if signal == 0 or len(df) == 0:
            return None

        last_close = float(df['close'].iloc[-1])
        n_digits = 3 if stock.get('stock_type') == 'Fund' else 2

        if signal == 1:
            entry = round(last_close * 0.995, n_digits)
            stop_loss = round(stock['support'] * 0.995, n_digits)
            take_profit = stock['resistance'] * 0.995
        else:
            entry = round(last_close * 1.005, n_digits)
            stop_loss = round(stock['resistance'] * 1.005, n_digits)
            take_profit = round(stock['support'] * 1.005, n_digits)

        # meta: 把最近一次判定时保留的元信息放入策略里，便于回测审计
        meta = {}
        try:
            meta = getattr(self, '_last_signal_meta', {}) or {}
        except Exception as ex:
            print(ex)
            meta = {}

        strategy = TradingStrategy(
            strategy_name=self.name,
            stock_code=stock.get('code'),
            stock_name=stock.get('name'),
            entry_patterns=['CHAN', 'ZONE', 'PEN', 'LINE'],
            exit_patterns=[],
            exchange=stock.get('exchange'),
            entry_price=float(entry),
            take_profit=float(take_profit),
            stop_loss=float(stop_loss),
            signal=signal
        )

        # 附加 meta 字典（如果 TradingStrategy 支持）
        try:
            # 一般 strategy 对象会接受额外字段或 meta；如果没有，请替换为 strategy.extra = meta
            setattr(strategy, 'meta', meta)
        except Exception as exception:
            print(exception)
            pass

        return strategy
