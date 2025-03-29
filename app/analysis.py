from flask import Blueprint, jsonify, request

from index import analyze_index, analyze_index_stocks
from stock import get_stock, analyze_stock

analysis = Blueprint('analysis', __name__, url_prefix='/analysis')


@analysis.route('/index', methods=['GET'])
def analysis_index_stocks():
    indexes = analyze_index()
    return jsonify(indexes), 200


@analysis.route('/index/stock', methods=['GET'])
def analysis_index():
    code = request.args.get('code')
    if code is None:
        return jsonify({'message': 'param code is required'}), 400

    stocks = analyze_index_stocks(code)
    return jsonify(stocks), 200


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
        return jsonify({'message': 'param code is required'}), 400

    # 根据代码获取股票信息
    stock = get_stock(code)
    # 检查股票信息是否找到
    if stock is None:
        return jsonify({'message': 'stock not found'}), 404

    # 分析股票信息
    analyze_stock(stock)
    # 返回分析后的股票信息
    return jsonify(stock), 200
