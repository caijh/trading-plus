import pandas_ta as ta

from app.calculate.service import get_distance, is_hammer_strict
from app.indicator.base import Indicator

BULLISH_PATTERNS = [
    # {'name': '3inside', 'description': '三日内线：一个三日反转形态，可以是看涨或看跌。'},
    # {'name': '3linestrike', 'description': '三线打击：一个四日的看涨持续形态。'},
    # {'name': '3outside', 'description': '三日外线：一个三日反转形态，可以是看涨或看跌。'},
    {'name': '3starsinsouth', 'description': '南方三星：一个三日的看涨反转形态。'},
    {'name': '3whitesoldiers', 'description': '三个白武士：一个三日的看涨反转形态。'},
    {'name': 'abandonedbaby', 'description': '弃婴：一个三日反转形态，可以是看涨或看跌。'},
    # {'name': 'belthold', 'description': '捉腰带线：一个一日反转形态，可以是看涨或看跌。'},
    {'name': 'breakaway', 'description': '脱离：一个五日持续形态，可以是看涨或看跌。'},
    # {'name': 'counterattack', 'description': '反击线：一个两日反转形态，可以是看涨或看跌。'},
    # {'name': 'dojistar', 'description': '十字星：一个两日反转形态，通常在长实体蜡烛线后出现。'},
    {'name': 'dragonflydoji', 'description': '蜻蜓十字星：开盘、最高和收盘价接近，表示潜在的看涨反转。'},
    # {'name': 'engulfing', 'description': '吞噬形态：一个两日反转形态，可以是看涨或看跌。'},
    # {'name': 'gapsidesidewhite', 'description': '上下并列双阳线：一个两日的看涨持续形态。'},
    {'name': 'hammer', 'description': '锤子线：一个单根蜡烛线的看涨反转形态。'},
    # {'name': 'harami', 'description': '怀抱线：一个两日反转形态，可以是看涨或看跌。'},
    # {'name': 'haramicross', 'description': '十字怀抱线：一个两日反转形态，其中包含一个十字星。'},
    # {'name': 'hikkake', 'description': '圈套：一个两日反转形态，可以是看涨或看跌。'},
    # {'name': 'hikkakemod', 'description': '修正圈套：圈套形态的变体。'},
    # {'name': 'homingpigeon', 'description': '家鸽：一个两日的看涨反转形态。'},
    # {'name': 'invertedhammer', 'description': '倒锤子线：一个单根蜡烛线的看涨反转形态。'},
    # {'name': 'kicking', 'description': '踢脚线：一个两日反转形态，可以是看涨或看跌。'},
    {'name': 'ladderbottom', 'description': '梯底：一个五日的看涨反转形态。'},
    # {'name': 'matchinglow', 'description': '匹敌低价：一个两日的看涨反转形态。'},
    {'name': 'mathold', 'description': '铺垫：一个五日的看涨持续形态。'},
    {'name': 'morningdojistar', 'description': '启明星十字星：一个三日的看涨反转形态。'},
    {'name': 'morningstar', 'description': '启明星：一个三日的看涨反转形态。'},
    # {'name': 'piercing', 'description': '刺透线：一个两日的看涨反转形态。'},
    # {'name': 'risefall3methods', 'description': '三升三降：一个五日持续形态，可以是看涨或看跌。'},
    # {'name': 'separatinglines', 'description': '分离线：一个两日持续形态，可以是看涨或看跌。'},
    {'name': 'sticksandwich', 'description': '夹心三明治：一个三日的看涨反转形态。'},
    # {'name': 'takuri', 'description': '捉腰带线：一种蜻蜓十字星或捉腰带线。'},
    # {'name': 'tasukigap', 'description': '跳空并列：一个两日持续形态，可以是看涨或看跌。'},
    # {'name': 'thrusting', 'description': '插入线：一个两日的看跌持续形态。'},
    {'name': 'tristar', 'description': '三星：由三个十字星组成的三日反转形态。'},
    # {'name': 'unique3river', 'description': '独有三河：一个三日的看涨反转形态。'},
    # {'name': 'xsidegap3methods', 'description': '跳空三法：一个五日持续形态，可以是看涨或看跌。'}
]

BEARISH_PATTERNS = [
    {'name': '2crows', 'description': '两只乌鸦：一个两日的看跌反转形态。'},
    {'name': '3blackcrows', 'description': '三只乌鸦：一个三日的看跌反转形态。'},
    {'name': '3inside', 'description': '三日内线：一个三日反转形态，可以是看涨或看跌。'},
    {'name': '3outside', 'description': '三日外线：一个三日反转形态，可以是看涨或看跌。'},
    {'name': 'abandonedbaby', 'description': '弃婴：一个三日反转形态，可以是看涨或看跌。'},
    {'name': 'advanceblock', 'description': '推进之区：一个三日的看跌反转形态。'},
    {'name': 'belthold', 'description': '捉腰带线：一个一日反转形态，可以是看涨或看跌。'},
    {'name': 'breakaway', 'description': '脱离：一个五日持续形态，可以是看涨或看跌。'},
    {'name': 'closingmarubozu', 'description': '收盘光头光脚：表示趋势强劲的单根蜡烛线。'},
    {'name': 'concealbabyswall', 'description': '藏婴墙：一个四日的看跌反转形态。'},
    {'name': 'counterattack', 'description': '反击线：一个两日反转形态，可以是看涨或看跌。'},
    {'name': 'darkcloudcover', 'description': '乌云盖顶：一个两日的看跌反转形态。'},
    {'name': 'doji', 'description': '十字星：开盘价和收盘价几乎相同，表示市场犹豫不决。'},
    {'name': 'dojistar', 'description': '十字星：一个两日反转形态，通常在长实体蜡烛线后出现。'},
    {'name': 'dragonflydoji', 'description': '蜻蜓十字星：开盘、最高和收盘价接近，表示潜在的看涨反转。'},
    {'name': 'engulfing', 'description': '吞噬形态：一个两日反转形态，可以是看涨或看跌。'},
    {'name': 'eveningdojistar', 'description': '黄昏十字星：一个三日的看跌反转形态。'},
    {'name': 'eveningstar', 'description': '黄昏之星：一个三日的看跌反转形态。'},
    {'name': 'gravestonedoji', 'description': '墓碑十字星：开盘、最低和收盘价接近，表示潜在的看跌反转。'},
    {'name': 'hangingman', 'description': '上吊线：一个单根蜡烛线的看跌反转形态。'},
    {'name': 'harami', 'description': '怀抱线：一个两日反转形态，可以是看涨或看跌。'},
    {'name': 'haramicross', 'description': '十字怀抱线：一个两日反转形态，其中包含一个十字星。'},
    {'name': 'highwave', 'description': '高浪线：影线很长，表示市场极度犹豫不决。'},
    {'name': 'hikkake', 'description': '圈套：一个两日反转形态，可以是看涨或看跌。'},
    {'name': 'hikkakemod', 'description': '修正圈套：圈套形态的变体。'},
    {'name': 'homingpigeon', 'description': '家鸽：一个两日的看涨反转形态。'},
    {'name': 'identical3crows', 'description': '三同鸦：一个三日的看跌反转形态。'},
    {'name': 'inneck', 'description': '颈内线：一个两日的看跌持续形态。'},
    {'name': 'inside', 'description': '内线形态：第二个蜡烛线完全包含在第一个蜡烛线内。'},
    {'name': 'invertedhammer', 'description': '倒锤子线：一个单根蜡烛线的看涨反转形态。'},
    {'name': 'kicking', 'description': '踢脚线：一个两日反转形态，可以是看涨或看跌。'},
    {'name': 'kickingbylength', 'description': '较长踢脚线：由较长蜡烛线组成的踢脚线形态。'},
    {'name': 'longleggeddoji', 'description': '长脚十字星：影线很长的十字星，表示高度犹豫不决。'},
    {'name': 'longline', 'description': '长蜡烛线：实体很长，表示强劲的趋势。'},
    {'name': 'marubozu', 'description': '光头光脚：没有影线，表示非常强烈的看涨或看跌情绪。'},
    {'name': 'matchinglow', 'description': '匹敌低价：一个两日的看涨反转形态。'},
    {'name': 'mathold', 'description': '铺垫：一个五日的看涨持续形态。'},
    {'name': 'morningdojistar', 'description': '启明星十字星：一个三日的看涨反转形态。'},
    {'name': 'morningstar', 'description': '启明星：一个三日的看涨反转形态。'},
    {'name': 'onneck', 'description': '颈上线：一个两日的看跌持续形态。'},
    {'name': 'rickshawman', 'description': '黄包车夫：一种长脚十字星形态。'},
    {'name': 'risefall3methods', 'description': '三升三降：一个五日持续形态，可以是看涨或看跌。'},
    {'name': 'separatinglines', 'description': '分离线：一个两日持续形态，可以是看涨或看跌。'},
    {'name': 'shootingstar', 'description': '射击之星：一个单根蜡烛线的看跌反转形态。'},
    # {'name': 'shortline', 'description': '短蜡烛线：实体很小，表示价格波动不大。'},
    {'name': 'spinningtop', 'description': '纺锤线：实体小，影线短，表示犹豫不决。'},
    {'name': 'stalledpattern', 'description': '停顿形态：一个三日的看跌反转形态。'},
    {'name': 'takuri', 'description': '捉腰带线：一种蜻蜓十字星或捉腰带线。'},
    {'name': 'tasukigap', 'description': '跳空并列：一个两日持续形态，可以是看涨或看跌。'},
    {'name': 'thrusting', 'description': '插入线：一个两日的看跌持续形态。'},
    {'name': 'tristar', 'description': '三星：由三个十字星组成的三日反转形态。'},
    {'name': 'unique3river', 'description': '独有三河：一个三日的看涨反转形态。'},
    {'name': 'upsidegap2crows', 'description': '向上跳空两只乌鸦：一个三日的看跌反转形态。'},
    {'name': 'xsidegap3methods', 'description': '跳空三法：一个五日持续形态，可以是看涨或看跌。'}
]


class Candlestick(Indicator):
    name = ''
    column = ''
    label = ''
    signal = 1
    weight = 0
    recent = 3

    def __init__(self, pattern, signal):
        self.signal = signal
        self.name = pattern['name']
        self.label = pattern['name']
        self.column = f'CDL_{self.name.upper()}'
        self.description = pattern['description']
        self.match_indexes = []

    def to_dict(self):
        match_indexes = []
        for match_index in self.match_indexes:
            match_indexes.append(match_index.strftime('%Y-%m-%d %H:%M:%S'))
        return {
            'name': self.name,
            'label': self.label,
            'description': self.description,
            'match_indexes': match_indexes
        }

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
        pattern_df = df.tail(60).copy()

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
            self.match_indexes.extend(matched.index.tolist())
            weight = get_distance(df, df.loc[self.match_indexes[-1]], df.iloc[-1])
            self.weight = self.recent + 1 - weight
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
    for PATTERN in BULLISH_PATTERNS:
        patterns.append(Candlestick(PATTERN, 1))

    return patterns


def get_bearish_candlestick_patterns():
    """
    创建并返回一系列蜡烛图形态的实例列表。

    这个函数负责初始化并返回一个列表，列表中包含了看跌形态的蜡烛图形态实例。
    """
    patterns = []
    for PATTERN in BEARISH_PATTERNS:
        patterns.append(Candlestick(PATTERN, -1))

    return patterns


class HammerCandlestick(Indicator):
    """
    锤子线形态检测器类

    用于检测K线图表中的锤子线形态，继承自Indicator基类
    """
    name = ''
    label = ''
    signal = 1
    weight = 1
    recent = 3

    def __init__(self):
        """
        初始化锤子线检测器
        """
        self.name = 'Hammer'
        self.label = 'Hammer'
        self.description = 'Hammer'
        self.match_indexes = []

    def match(self, stock, df, trending, direction):
        """
        检测锤子线形态

        Args:
            stock: 股票对象
            df: K线数据DataFrame
            trending: 趋势信息
            direction: 方向信息

        Returns:
            bool: 如果检测到锤子线形态返回True，否则返回False
        """
        # 获取最近recent期的K线数据
        k_lines = df.tail(self.recent).copy()
        k_line = None
        k_index = None

        # 从最近到旧的顺序遍历k_lines, 判断是否是hammer形态
        # 如果发现多个锤子线，选择最低点的那个
        for i in range(self.recent - 1, -1, -1):
            if is_hammer_strict(k_lines.iloc[i]):
                if k_line is None:
                    k_line = k_lines.iloc[i]
                    k_index = k_lines.index[i]
                else:
                    if k_line['low'] > k_lines.iloc[i]['low']:
                        k_line = k_lines.iloc[i]
                        k_index = k_lines.index[i]

        # 如果找到锤子线形态，记录其索引并返回True
        if k_line is not None:
            self.match_indexes.append(k_index)
            return True
        return False
