import pandas_ta as ta

ALL_PATTERNS = [
    {"name": "2crows", "description": "两只乌鸦"},
    {"name": "3blackcrows", "description": "三只乌鸦"},
    {"name": "3inside", "description": "三内升/三内降"},
    {"name": "3linestrike", "description": "三线打击"},
    {"name": "3outside", "description": "三外升/三外降"},
    {"name": "3starsinsouth", "description": "南方三星"},
    {"name": "3whitesoldiers", "description": "三白兵"},
    {"name": "abandonedbaby", "description": "弃婴形态"},
    {"name": "advanceblock", "description": "上升受阻"},
    {"name": "belthold", "description": "腰带线"},
    {"name": "breakaway", "description": "脱离形态"},
    {"name": "closingmarubozu", "description": "收盘光头光脚阳线/阴线"},
    {"name": "concealbabyswall", "description": "隐藏吞没婴儿"},
    {"name": "counterattack", "description": "反击线"},
    {"name": "darkcloudcover", "description": "乌云盖顶"},
    {"name": "dojistar", "description": "十字星"},
    {"name": "dragonflydoji", "description": "蜻蜓十字/T字线"},
    {"name": "engulfing", "description": "吞没形态"},
    {"name": "eveningdojistar", "description": "黄昏十字星"},
    {"name": "eveningstar", "description": "黄昏星"},
    {"name": "gapsidesidewhite", "description": "向上/向下并列阳线"},
    {"name": "gravestonedoji", "description": "墓碑十字"},
    {"name": "hammer", "description": "锤头线"},
    {"name": "hangingman", "description": "上吊线"},
    {"name": "harami", "description": "母子线"},
    {"name": "haramicross", "description": "十字孕线"},
    {"name": "highwave", "description": "高浪线"},
    {"name": "hikkake", "description": "陷阱形态"},
    {"name": "hikkakemod", "description": "修正陷阱形态"},
    {"name": "homingpigeon", "description": "归巢鸽"},
    {"name": "identical3crows", "description": "等长三鸦"},
    {"name": "inneck", "description": "颈内线"},
    # {"name": "inside", "description": "内包线"},
    {"name": "invertedhammer", "description": "倒锤头线"},
    {"name": "kicking", "description": "反冲形态"},
    {"name": "kickingbylength", "description": "按长度判断的反冲形态"},
    {"name": "ladderbottom", "description": "梯底形态"},
    {"name": "longleggeddoji", "description": "长脚十字"},
    {"name": "longline", "description": "长蜡烛线"},
    {"name": "marubozu", "description": "光头光脚阳线/阴线"},
    {"name": "matchinglow", "description": "等低线"},
    {"name": "mathold", "description": "保持形态"},
    {"name": "morningdojistar", "description": "晨星十字星"},
    {"name": "morningstar", "description": "晨星"},
    {"name": "onneck", "description": "颈上线"},
    {"name": "piercing", "description": "刺透线"},
    {"name": "rickshawman", "description": "黄包车夫线（长脚十字）"},
    {"name": "risefall3methods", "description": "三方法（上升/下降）"},
    {"name": "separatinglines", "description": "分离线"},
    {"name": "shootingstar", "description": "流星线"},
    {"name": "shortline", "description": "短蜡烛线"},
    {"name": "spinningtop", "description": "纺锤线"},
    {"name": "stalledpattern", "description": "停顿形态"},
    {"name": "sticksandwich", "description": "条形三明治"},
    {"name": "takuri", "description": "探水线"},
    {"name": "tasukigap", "description": "切入缺口"},
    {"name": "thrusting", "description": "插入线"},
    {"name": "tristar", "description": "三星形态"},
    {"name": "unique3river", "description": "奇特三河床"},
    {"name": "upsidegap2crows", "description": "上升缺口两鸦"},
    {"name": "xsidegap3methods", "description": "横向缺口三方法"}
]


class Candlestick:
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

    def match(self, stock, prices, df):
        """
        判断给定股票的最近几个交易日中是否出现了特定的K线形态，并记录出现的日期。

        :param stock: 股票字典，将在其中记录形态出现的日期。
        :param prices: 股票价格数据（未使用，但保留参数结构）。
        :param df: 包含股票历史数据的DataFrame，至少包括['open', 'high', 'low', 'close']列。
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
            candlestick_patterns = {
                'name': self.name,
                'description': self.description,
                'dates': matched.index.strftime('%Y-%m-%d').tolist()
            }
            stock['patterns_candlestick'].append(candlestick_patterns)
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
        patterns.append(Candlestick(PATTERN, 1))

    return patterns


def get_bearish_candlestick_patterns():
    """
    创建并返回一系列蜡烛图形态的实例列表。

    这个函数负责初始化并返回一个列表，列表中包含了看跌形态的蜡烛图形态实例。
    """
    patterns = []
    for PATTERN in ALL_PATTERNS:
        patterns.append(Candlestick(PATTERN, -1))

    return patterns
