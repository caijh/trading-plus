from flask import jsonify, Blueprint

from extensions import executor
from strategy.service import run_generate_strategy

strategy = Blueprint('strategy', __name__, url_prefix='/strategy')


@strategy.route('/generate-next-check-history', methods=['GET'])
def generate_next_check_history():
    executor.submit(run_generate_strategy)

    # 返回任务id和200状态码
    return jsonify({'code': 0, 'msg': 'Job running'}), 200
