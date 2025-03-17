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
    code = request.args.get('code')
    if code is None:
        return jsonify({'message': 'param code is required'}), 400

    stock = get_stock(code)
    if stock is None:
        return jsonify({'message': 'stock not found'}), 404

    analyze_stock(stock)
    return jsonify(stock), 200
