from analysis.service import analyze_stock
from environment.service import env_vars
from request.service import http_get_with_retries
from stock.service import KType, get_stock


def get_stock_index_list():
    """
    获取股票指数列表。

    本函数从预设的交易数据URL中获取股票指数列表数据。URL由环境变量TRADING_DATA_URL指定。

    Returns:
        list: 股票指数列表，如果请求失败或数据源返回错误，返回空列表。
    """
    # 构造请求URL
    url = f'{env_vars.TRADING_DATA_URL}/index/list'
    print(f'从数据源获指示列表数据，url: {url}')
    # 发起GET请求，获取数据，并将响应内容解析为JSON格式
    return http_get_with_retries(url, 3, [])


def get_index_stocks(code):
    """
    根据指数代码获取指数成分股列表。

    参数:
    code (str): 指数代码。

    返回:
    list: 指数成分股列表，如果请求失败或数据不可用，则返回空列表。
    """
    # 从环境变量中获取交易数据URL
    # 构造获取指数成分股的URL
    url = f'{env_vars.TRADING_DATA_URL}/index/{code}/stocks'

    print(f'从数据源获取指数成分股数据，url: {url}')

    return http_get_with_retries(url, 3, [])


def analyze_index(signal):
    """
    分析股票指数

    该函数通过获取股票指数列表，并对每个指数进行分析，以找出具有特定模式的指数。
    它主要关注的是日K线图中的模式。

    Returns:
        list: 包含有效模式的股票指数列表。
    """
    # 获取股票指数列表
    data = get_stock_index_list()
    indexes = []
    for index in data:
        # 分析每个指数的日K线图模式
        if signal is not None:
            signal = int(signal)
        else:
            signal = 1
        index['stock_type'] = 'Index'
        stock = analyze_stock(index, k_type=KType.DAY, signal=signal)
        indexes.append(stock)

    return indexes


def analyze_index_stocks(code):
    """
    分析指数包含的股票，并返回具有特定模式的股票列表。

    参数:
    code (str): 指数的代码。

    返回:
    list: 包含特定模式的股票信息列表。
    """
    # 获取指数包含的股票数据
    data = get_index_stocks(code)
    stocks = []
    # 遍历指数中的每只股票
    for item in data:
        # 构建股票字典，包含股票代码和名称
        # 根据代码获取股票信息
        stock_code = item['stock_code']
        stock = get_stock(stock_code)
        # 分析股票的日K线图
        analyze_stock(stock, k_type=KType.DAY)
        # 如果股票中发现有模式，则将其添加到stocks列表中
        if len(stock['patterns']) > 0:
            stocks.append(stock)

    return stocks
