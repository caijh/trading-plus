import requests

from analysis.service import analyze_stock
from environment.service import env_vars
from stock.service import KType


def get_funds(exchange):
    url = f'{env_vars.TRADING_DATA_URL}/exchange/{exchange}/funds'
    print(f'从交易所获取基金列表数据，url: {url}')
    # 尝试最多3次请求
    for attempt in range(3):
        try:
            # 发送GET请求并解析响应内容为JSON格式
            data = requests.get(url).json()
            # 检查响应状态码是否为0，表示请求成功
            if data['code'] == 0:
                # 提取并返回基金数据
                return data['data']
        except requests.RequestException as e:
            print(f'Request failed: {e}. Retrying... {attempt + 1}')
    # 如果所有尝试都失败，返回空列表
    return []


def analyze_funds(exchange):
    """
    分析给定交易所，返回具有特定模式的基金列表。

    该函数首先从指定交易所获取所有基金列表，然后逐个分析每只基金。
    分析时，会特别关注在日K线图中出现的模式。只有那些具有至少一个识别模式的股票才会被记录并返回。

    参数:
    exchange: str, 指定要分析的交易所名称。

    返回:
    list, 包含具有特定模式的股票信息列表。
    """
    # 获取指定交易所的所有股票资金数据
    data = get_funds(exchange)

    # 初始化用于存储具有分析模式的股票列表
    funds = []

    # 遍历每只股票进行分析
    for item in data:
        # 将数据项初始化为股票对象，这里假设股票对象可以直接从数据项转换而来
        stock = item
        stock['stock_type'] = 'Fund'

        # 调用函数分析股票，专注于日K线图中的模式
        try:
            analyze_stock(stock, k_type=KType.DAY, buy_ma_weight=3, buy_volume_weight=2)
            # 如果股票中发现了至少一个模式，则将其添加到结果列表中
            if len(stock['patterns']) > 0:
                funds.append(stock)
        except Exception as e:
            print(f'Failed to analyze stock: {e}')

    # 返回具有特定模式的股票列表
    return funds
