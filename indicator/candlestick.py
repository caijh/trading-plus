import pandas_ta as ta

from indicator.base import Indicator

ALL_PATTERNS = [
    {"name": "2crows", "description": "两只乌鸦", "signal": -1, "weight": 0},
    {"name": "3blackcrows", "description": "三只乌鸦", "signal": -1, "weight": 0},
    {"name": "3inside", "description": "三内升/三内降", "signal": 0, "weight": 0},
    {"name": "3linestrike", "description": "三线打击", "signal": 1, "weight": 0},
    {"name": "3outside", "description": "三外升/三外降", "signal": 1, "weight": 0},
    {"name": "3starsinsouth", "description": "南方三星", "signal": 1, "weight": 0},
    {"name": "3whitesoldiers", "description": "三白兵", "signal": 1, "weight": 1},
    {"name": "abandonedbaby", "description": "弃婴形态", "signal": 1, "weight": 1},
    {"name": "advanceblock", "description": "上升受阻", "signal": -1, "weight": 0},
    {"name": "belthold", "description": "腰带线", "signal": 0, "weight": 0},
    {"name": "breakaway", "description": "脱离形态", "signal": 0, "weight": 0},
    {"name": "closingmarubozu", "description": "收盘光头光脚阳线/阴线", "signal": 0, "weight": 0},
    {"name": "concealbabyswall", "description": "隐藏吞没婴儿", "signal": 1, "weight": 0},
    {"name": "counterattack", "description": "反击线", "signal": 0, "weight": 1},
    {"name": "darkcloudcover", "description": "乌云盖顶", "signal": -1, "weight": 0},
    {"name": "dojistar", "description": "十字星", "signal": 0, "weight": 0},
    {"name": "dragonflydoji", "description": "蜻蜓十字/T字线", "signal": 1, "weight": 0},
    {"name": "engulfing", "description": "吞没形态", "signal": 0, "weight": 1},
    {"name": "eveningdojistar", "description": "黄昏十字星", "signal": -1, "weight": 0},
    {"name": "eveningstar", "description": "黄昏星", "signal": -1, "weight": 0},
    {"name": "gapsidesidewhite", "description": "向上/向下并列阳线", "signal": 1, "weight": 0},
    {"name": "gravestonedoji", "description": "墓碑十字", "signal": -1, "weight": 0},
    {"name": "hammer", "description": "锤子线", "signal": 1, "weight": 1},
    {"name": "hangingman", "description": "上吊线", "signal": -1, "weight": 0},
    {"name": "harami", "description": "母子线", "signal": 0, "weight": 0},
    {"name": "haramicross", "description": "十字孕线", "signal": 0, "weight": 0},
    {"name": "highwave", "description": "高浪线", "signal": 0, "weight": 0},
    {"name": "hikkake", "description": "陷阱形态", "signal": 1, "weight": 0},
    {"name": "hikkakemod", "description": "修正陷阱形态", "signal": 1, "weight": 0},
    {"name": "homingpigeon", "description": "归巢鸽", "signal": 1, "weight": 0},
    {"name": "identical3crows", "description": "等长三鸦", "signal": -1, "weight": 0},
    {"name": "inneck", "description": "颈内线", "signal": -1, "weight": 0},
    {"name": "inside", "description": "内包线", "signal": 0, "weight": 0},
    {"name": "invertedhammer", "description": "倒锤头线", "signal": 0, "weight": 0},
    {"name": "kicking", "description": "反冲形态", "signal": 0, "weight": 0},
    {"name": "kickingbylength", "description": "按长度判断的反冲形态", "signal": 0, "weight": 0},
    {"name": "ladderbottom", "description": "梯底形态", "signal": 1, "weight": 0},
    {"name": "longleggeddoji", "description": "长脚十字", "signal": 0, "weight": 0},
    {"name": "longline", "description": "长蜡烛线", "signal": 0, "weight": 0},
    {"name": "marubozu", "description": "光头光脚阳线/阴线", "signal": 0, "weight": 0},
    {"name": "matchinglow", "description": "等低线", "signal": 1, "weight": 0},
    {"name": "mathold", "description": "保持形态", "signal": 1, "weight": 0},
    {"name": "morningdojistar", "description": "晨星十字星", "signal": 1, "weight": 1},
    {"name": "morningstar", "description": "晨星", "signal": 1, "weight": 1},
    {"name": "onneck", "description": "颈上线", "signal": -1, "weight": 0},
    {"name": "piercing", "description": "刺透线", "signal": 1, "weight": 1},
    {"name": "rickshawman", "description": "黄包车夫线（长脚十字）", "signal": 0, "weight": 0},
    {"name": "risefall3methods", "description": "三方法（上升/下降）", "signal": 0, "weight": 0},
    {"name": "separatinglines", "description": "分离线", "signal": 1, "weight": 0},
    {"name": "shootingstar", "description": "流星线", "signal": -1, "weight": 0},
    {"name": "shortline", "description": "短蜡烛线", "signal": 0, "weight": 0},
    {"name": "spinningtop", "description": "纺锤线", "signal": 0, "weight": 0},
    {"name": "stalledpattern", "description": "停顿形态", "signal": -1, "weight": 0},
    {"name": "sticksandwich", "description": "条形三明治", "signal": 1, "weight": 0},
    {"name": "takuri", "description": "探水线", "signal": 1, "weight": 1},
    {"name": "tasukigap", "description": "切入缺口", "signal": 1, "weight": 0},
    {"name": "thrusting", "description": "插入线", "signal": -1, "weight": 0},
    {"name": "tristar", "description": "三星形态", "signal": 0, "weight": 1},
    {"name": "unique3river", "description": "奇特三河床", "signal": 1, "weight": 0},
    {"name": "upsidegap2crows", "description": "上升缺口两鸦", "signal": -1, "weight": 0},
    {"name": "xsidegap3methods", "description": "横向缺口三方法", "signal": 0, "weight": 0}
]


class Candlestick(Indicator):
    name = ''
    column = ''
    label = ''
    signal = 1
    weight = 1
    recent = 3

    def __init__(self, pattern, signal):
        self.signal = signal
        self.name = pattern['name']
        self.label = pattern['name']
        self.column = f'CDL_{self.name.upper()}'
        self.description = pattern['description']

    def match(self, stock, df, trending, direction):
        """
        判断给定股票的最近几个交易日中是否出现了特定的K线形态，并记录出现的日期。

        :param stock: 股票字典，将在其中记录形态出现的日期。
        :param df: 包含股票历史数据的DataFrame，至少包括['open', 'high', 'low', 'close']列。
        :param trending 趋势
        :param direction 方向
        :return: 布尔值，表示是否匹配到了指定的K线形态。
        """
        # 用最近20根K线计算形态
        pattern_df = df.tail(20).copy()

        # 计算K线形态，结果列为 self.column
        pattern_df[self.column] = ta.cdl_pattern(
            pattern_df['open'], pattern_df['high'], pattern_df['low'], pattern_df['close'], name=self.name
        )

        # 检查最近 self.recent 根K线是否匹配信号
        recent_pattern = pattern_df.tail(self.recent)

        if self.signal == 1:
            matched = recent_pattern[recent_pattern[self.column] > 0]
        else:
            matched = recent_pattern[recent_pattern[self.column] < 0]

        # 提取匹配日期，并写入 stock 中
        if not matched.empty:
            return True
        else:
            return False


def get_bullish_candlestick_patterns():
    """
    创建并返回一系列蜡烛图形态的实例列表。

    这个函数负责初始化并返回一个列表，列表中包含了不同类型的蜡烛图形态实例。
    这些形态实例包括锤头、十字星、看涨吞没、刺透和上升窗口等形态。
    """
    patterns = []
    for PATTERN in ALL_PATTERNS:
        if (PATTERN['signal'] == 1 or PATTERN['signal'] == 0) and PATTERN['weight'] > 0:
            patterns.append(Candlestick(PATTERN, 1))

    return patterns


def get_bearish_candlestick_patterns():
    """
    创建并返回一系列蜡烛图形态的实例列表。

    这个函数负责初始化并返回一个列表，列表中包含了看跌形态的蜡烛图形态实例。
    """
    patterns = []
    for PATTERN in ALL_PATTERNS:
        if PATTERN['signal'] == -1 or PATTERN['signal'] == 0:
            patterns.append(Candlestick(PATTERN, -1))

    return patterns
