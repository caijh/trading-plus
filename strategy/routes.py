from flask import jsonify, Blueprint, request

from extensions import executor
from strategy.model import TradingStrategy
from strategy.service import run_generate_strategy

strategy_blueprint = Blueprint('strategy', __name__, url_prefix='/strategy')


@strategy_blueprint.route('/generate-next-check-history', methods=['GET'])
def generate_next_check_history():
    executor.submit(run_generate_strategy)

    # 返回任务id和200状态码
    return jsonify({'code': 0, 'msg': 'Job running'}), 200


@strategy_blueprint.route('/trading', methods=['POST'])
def get_analyzed_stocks():
    try:
        # 获取分页参数
        page = request.args.get('page', default=1, type=int)
        page_size = request.args.get('page_size', default=10, type=int)

        # 从请求体中获取 exchange 和 code 参数
        req_body = request.get_json()
        exchange = req_body.get('exchange') if req_body else None
        code = req_body.get('code') if req_body else None

        # 构建基础查询
        query = TradingStrategy.query.order_by(TradingStrategy.updated_at.desc())

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
            "items": [strategy.to_dict() for strategy in pagination.items]
        }

        # 返回格式化数据
        return jsonify({"code": 0, 'data': data, "msg": "success"})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500
