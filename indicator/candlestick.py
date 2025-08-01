import pandas_ta as ta

ALL_PATTERNS = [
    "2crows",  # 两只乌鸦
    "3blackcrows",  # 三只乌鸦
    "3inside",  # 三内升/三内降
    "3linestrike",  # 三线打击
    "3outside",  # 三外升/三外降
    "3starsinsouth",  # 南方三星
    "3whitesoldiers",  # 三白兵
    "abandonedbaby",  # 弃婴形态
    "advanceblock",  # 上升受阻
    "belthold",  # 腰带线
    "breakaway",  # 脱离形态
    "closingmarubozu",  # 收盘光头光脚阳线/阴线
    "concealbabyswall",  # 隐藏吞没婴儿
    "counterattack",  # 反击线
    "darkcloudcover",  # 乌云盖顶
    "dojistar",  # 十字星
    "dragonflydoji",  # 蜻蜓十字/T字线
    "engulfing",  # 吞没形态
    "eveningdojistar",  # 黄昏十字星
    "eveningstar",  # 黄昏星
    "gapsidesidewhite",  # 向上/向下并列阳线
    "gravestonedoji",  # 墓碑十字
    "hammer",  # 锤头线
    "hangingman",  # 上吊线
    "harami",  # 母子线
    "haramicross",  # 十字孕线
    "highwave",  # 高浪线
    "hikkake",  # 陷阱形态
    "hikkakemod",  # 修正陷阱形态
    "homingpigeon",  # 归巢鸽
    "identical3crows",  # 等长三鸦
    "inneck",  # 颈内线
    "inside",  # 内包线
    "invertedhammer",  # 倒锤头线
    "kicking",  # 反冲形态
    "kickingbylength",  # 按长度判断的反冲形态
    "ladderbottom",  # 梯底形态
    "longleggeddoji",  # 长脚十字
    "longline",  # 长蜡烛线
    "marubozu",  # 光头光脚阳线/阴线
    "matchinglow",  # 等低线
    "mathold",  # 保持形态
    "morningdojistar",  # 晨星十字星
    "morningstar",  # 晨星
    "onneck",  # 颈上线
    "piercing",  # 刺透线
    "rickshawman",  # 黄包车夫线（长脚十字）
    "risefall3methods",  # 三方法（上升/下降）
    "separatinglines",  # 分离线
    "shootingstar",  # 流星线
    "shortline",  # 短蜡烛线
    "spinningtop",  # 纺锤线
    "stalledpattern",  # 停顿形态
    "sticksandwich",  # 条形三明治
    "takuri",  # 探水线
    "tasukigap",  # 切入缺口
    "thrusting",  # 插入线
    "tristar",  # 三星形态
    "unique3river",  # 奇特三河床
    "upsidegap2crows",  # 上升缺口两鸦
    "xsidegap3methods"  # 横向缺口三方法
]


class Candlestick:
    name = ''
    column = ''
    label = ''
    signal = 1
    weight = 1
    recent = 5

    def __init__(self, name, label_, column, signal):
        self.signal = signal
        self.name = name
        self.label = label_
        self.column = column

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
        patterns.append(Candlestick(PATTERN, PATTERN, f'CDL_{PATTERN.upper()}', 1))

    return patterns


def get_bearish_candlestick_patterns():
    """
    创建并返回一系列蜡烛图形态的实例列表。

    这个函数负责初始化并返回一个列表，列表中包含了看跌形态的蜡烛图形态实例。
    """
    patterns = []
    for PATTERN in ALL_PATTERNS:
        patterns.append(Candlestick(PATTERN, PATTERN, f'CDL_{PATTERN.upper()}', -1))

    return patterns
