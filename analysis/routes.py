from flask import jsonify, request, Blueprint

from analysis.model import AnalyzedStock
from analysis.service import save_analyzed_stocks, analyze_stock
from extensions import executor
from fund.service import analyze_funds
from index.service import analyze_index, analyze_index_stocks
from stock.service import get_stock, KType
from strategy.service import generate_strategies

analysis = Blueprint('analysis', __name__, url_prefix='/analysis')


@analysis.route('/index', methods=['GET'])
def analysis_index_stocks():
    """
    分析指数股票
    该函数响应GET请求，分析索引股票数据，并以JSON格式返回分析结果

    Returns:
        tuple: 包含响应体和状态码的元组
        - response body: 包含分析结果的JSON字符串
        - status code: HTTP状态码，200表示成功
    """
    signal = request.args.get('signal')
    # 调用analyze_index函数进行指数分析
    indexes = analyze_index(signal)
    # 将分析结果序列化为JSON，并返回200状态码表示成功
    return jsonify({'code': 0, 'data': indexes, 'msg': 'success'}), 200


@analysis.route('/index/stock', methods=['GET'])
def analysis_index():
    """
    分析指数中成分股。

    该函数通过GET请求接收一个code参数，用于指定指数代码。
    然后调用analyze_index_stocks函数来获取该指数的成分股信息，并以JSON格式返回。

    Returns:
        如果请求中缺少code参数，则返回错误信息和400状态码。
        否则，返回指数的成分股信息和200状态码。
    """
    # 从请求参数中获取股票指数代码
    code = request.args.get('code')
    # 检查是否提供了code参数
    if code is None:
        # 如果没有提供code参数，返回错误信息和400状态码
        return jsonify({'msg': 'Param code is required'}), 400

    stock = get_stock(code)

    # 检查股票信息是否找到
    if stock is None:
        return jsonify({'msg': 'stock not found'}), 404

    # 分析股票信息, 是否有买入信号
    analyze_stock(stock)
    if len(stock['patterns']) == 0:
        return jsonify({'code': 0, 'msg': 'Index pattern not match, analysis_index_task not run.'}), 200

    future = executor.submit(analysis_index_task, code)

    # 返回任务id和200状态码
    return jsonify({'code': 0, 'msg': 'Job running'}), 200


def analysis_index_task(index):
    # 调用analyze_index_stocks函数获取指数成分股信息
    stocks = analyze_index_stocks(index)

    save_analyzed_stocks(stocks)

    print("🚀 分析指数中股票完成!!!")

    generate_strategies(stocks)

    return stocks


@analysis.route('/stock', methods=['GET'])
def analysis_stock():
    """
    股票分析视图函数。

    该函数处理股票分析请求，接收股票代码作为查询参数，
    并返回股票分析结果。如果未提供股票代码或股票代码无效，
    则返回相应的错误信息和状态码。

    Returns:
        tuple: 包含响应体和状态码的元组。
               响应体为JSON格式，包含股票分析结果或错误信息。
    """
    # 获取查询参数中的股票代码
    code = request.args.get('code')
    # 检查股票代码是否提供
    if code is None:
        return jsonify({'msg': 'param code is required'}), 400

    # 根据代码获取股票信息
    stock = get_stock(code)
    # 检查股票信息是否找到
    if stock is None:
        return jsonify({'msg': 'stock not found'}), 404

    # 分析股票信息, 是否有买入信号
    analyze_stock(stock)
    if len(stock['patterns']) == 0:
        # 分析股票是否有卖出信号
        analyze_stock(stock, k_type=KType.DAY, signal=-1)
        if len(stock['patterns']) > 0:
            stock['signal'] = -1
    else:
        stock['signal'] = 1

    # 返回分析后的股票信息
    return jsonify({'code': 0, 'data': stock, 'msg': 'success'}), 200


def analysis_funds_task(exchange):
    """
    分析基金任务

    该函数负责调用分析基金的函数，并将分析结果写入数据库

    参数:
    exchange (str): 交易所名称，用于指定要分析的市场

    返回:
    stocks (list): 分析后的股票列表
    """
    stocks = analyze_funds(exchange)

    # 将分析后的股票列表写入数据库
    save_analyzed_stocks(stocks)

    generate_strategies(stocks)

    print("🚀 分析基金ETF完成!!!")

    # 返回分析后的股票列表
    return stocks


@analysis.route('/funds', methods=['GET'])
def analysis_funds():
    # 从请求参数中获取股票指数代码
    exchange = request.args.get('exchange')
    # 检查是否提供了code参数
    if exchange is None:
        # 如果没有提供code参数，返回错误信息和400状态码
        return jsonify({'msg': 'Param exchange is required'}), 400

    index = None
    if exchange == 'SSE' or exchange == 'SZSE':
        index = '000001.SH'
    elif exchange == 'HKEX':
        index = 'HSI.HK'
    elif exchange == 'NASDAQ':
        index = 'SPX.NS'

    exec_analyze_funds = True
    if index is not None:
        # 根据代码获取股票信息
        stock = get_stock(index)
        # 检查股票信息是否找到
        if stock is None:
            return jsonify({'msg': 'stock not found'}), 404

        analyze_stock(stock)
        if len(stock['patterns']) == 0:
            # 分析股票是否有卖出信号
            analyze_stock(stock, k_type=KType.DAY, signal=-1)
            if len(stock['patterns']) == 0:
                exec_analyze_funds = False

    if not exec_analyze_funds:
        return jsonify({'code': 0, 'msg': 'Index pattern not match, analysis_funds_task not run.'}), 200

    executor.submit(analysis_funds_task, exchange)

    # 返回任务id和200状态码
    return jsonify({'code': 0, 'msg': 'Job running'}), 200


@analysis.route('/analyzed', methods=['POST'])
def get_analyzed_stocks():
    try:
        # 获取分页参数
        page = request.args.get('page', default=1, type=int)
        page_size = request.args.get('page_size', default=10, type=int)
        req_body = request.get_json()
        exchange = req_body.get('exchange') if req_body else None
        code = req_body.get('code') if req_body else None
        # 构建基础查询
        query = AnalyzedStock.query.order_by(AnalyzedStock.updated_at.desc())

        # 按 exchange 和 code 添加过滤条件（如果存在）
        if exchange:
            query = query.filter_by(exchange=exchange)
        if code:
            query = query.filter_by(code=code)
        # 查询数据并分页
        pagination = query.paginate(
            page=page,
            per_page=page_size,
            error_out=False
        )
        data = {
            "total": pagination.total,
            "page_num": pagination.pages,
            "page": pagination.page,
            "page_size": pagination.per_page,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
            "items": [stock.to_dict() for stock in pagination.items]
        }
        # 返回格式化数据
        return jsonify({"code": 0, 'data': data, "msg": "success"})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500
