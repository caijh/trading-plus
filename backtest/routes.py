from flask import Blueprint, request, jsonify

from backtest.analyzer import evaluate_strategy
from backtest.runner import alpha_run_backtest

backtest_blueprint = Blueprint('backtest', __name__, url_prefix='/backtest')


@backtest_blueprint.route('/strategy', methods=['GET'])
def analysis_stock():
    code = request.args.get('stock_code')
    # 检查股票代码是否提供
    if code is None:
        return jsonify({'msg': 'param code is required'}), 400

    strategy_name = request.args.get('strategy_name')
    # 检查股票代码是否提供
    if strategy_name is None:
        return jsonify({'msg': 'param strategy_name is required'}), 400

    # 根据代码获取股票信息
    # strategy = get_strategy_by_stock_code(code)
    # # 检查股票信息是否找到
    # if strategy is None:
    #     return jsonify({'msg': 'strategy not found'}), 404

    results, win_patterns, loss_patterns, trending_list, direction_list = alpha_run_backtest(code, strategy_name)
    print(win_patterns)
    print(loss_patterns)
    print(trending_list)
    print(direction_list)
    result = evaluate_strategy(results)

    # 返回分析后的股票信息
    return jsonify({'code': 0, 'data': result, 'msg': 'success'}), 200
