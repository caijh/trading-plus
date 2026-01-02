from fastapi import APIRouter
from starlette.responses import JSONResponse

from app.backtest.analyzer import evaluate_strategy
from app.backtest.runner import alpha_run_backtest
from app.core.logger import logger

router = APIRouter()


@router.get('/strategy')
def analysis_stock(stick_code: str = None, strategy_name: str = None):
    # 检查股票代码是否提供
    if stick_code is None:
        return JSONResponse(
            status_code=400,
            content={"msg": "param code is required"}
        )

    # 检查股票代码是否提供
    if strategy_name is None:
        return JSONResponse(
            status_code=400,
            content={"msg": "param strategy_name is required"}
        )

    # 根据代码获取股票信息
    # strategy = get_strategy_by_stock_code(code)
    # # 检查股票信息是否找到
    # if strategy is None:
    #     return jsonify({'msg': 'strategy not found'}), 404

    results, win_patterns, loss_patterns, trending_list, direction_list = alpha_run_backtest(stick_code, strategy_name)
    logger.info(win_patterns)
    logger.info(loss_patterns)
    logger.info(trending_list)
    logger.info(direction_list)
    result = evaluate_strategy(results)

    # 返回分析后的股票信息
    return {'code': 0, 'data': result, 'msg': 'success'}
