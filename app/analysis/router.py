import threading

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app.analysis.service import save_analyzed_stocks, get_page_analyzed_stocks
from app.core.dependencies import get_db
from app.core.logger import logger
from app.fund.service import analyze_funds
from app.index.service import analyze_index, analyze_index_stocks
from app.stock.service import KType, get_stock
from app.strategy.service import analyze_stock, generate_strategies

analysis_router = APIRouter()


@analysis_router.get('/index')
async def analysis_index_stocks():
    """
    分析指数
    该函数响应GET请求，分析索引股票数据，并以JSON格式返回分析结果

    Returns:
        tuple: 包含响应体和状态码的元组
        - response body: 包含分析结果的JSON字符串
        - status code: HTTP状态码，200表示成功
    """
    # 调用analyze_index函数进行指数分析
    indexes = analyze_index()
    # 将分析结果序列化为JSON，并返回200状态码表示成功
    return {'code': 0, 'data': indexes, 'msg': 'success'}


@analysis_router.get('/index/stock')
async def analysis_index(db: Session = Depends(get_db),
                         code: str = None):
    """
    分析指数中成分股。

    该函数通过GET请求接收一个code参数，用于指定指数代码。
    然后调用analyze_index_stocks函数来获取该指数的成分股信息，并以JSON格式返回。

    Returns:
        如果请求中缺少code参数，则返回错误信息和400状态码。
        否则，返回指数的成分股信息和200状态码。
    """
    # 从请求参数中获取股票指数代码
    # 检查是否提供了code参数
    if code is None:
        # 如果没有提供code参数，返回错误信息和400状态码
        return JSONResponse(
            status_code=400,
            content={"msg": "Param code is required"}
        )

    stock = get_stock(code)

    # 检查股票信息是否找到
    if stock is None:
        return JSONResponse(
            status_code=404,
            content={"msg": "Stock not found"}
        )

    strategy = analyze_stock(stock, k_type=KType.DAY)
    if strategy is None:
        if stock['exchange'] == 'SZSE' or stock['exchange'] == 'SSE':
            return JSONResponse(
                status_code=200,
                content={"msg": "Index pattern not match, analysis_index_task not run.", "code": 0}
            )
    else:
        if (stock['exchange'] == 'SZSE' or stock['exchange'] == 'SSE') and strategy.signal != 1:
            return JSONResponse(
                status_code=200,
                content={"msg": "Index pattern not match, analysis_index_task not run.", "code": 0}
            )
        elif strategy.signal == -1:
            return JSONResponse(
                status_code=200,
                content={"msg": "Index pattern not match, analysis_index_task not run.", "code": 0}
            )

    thread = threading.Thread(target=analysis_index_task, args=(code, db))
    thread.start()

    return {'code': 0, 'msg': 'Job running'}


def analysis_index_task(index, db: Session):
    stocks = analyze_index_stocks(index)
    save_analyzed_stocks(stocks, db)
    logger.info("🚀 分析指数中股票完成!!!")
    generate_strategies(stocks, db)


@analysis_router.get('/stock')
async def analysis_stock(code: str = None):
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
    # 检查股票代码是否提供
    if code is None:
        return JSONResponse(
            status_code=200,
            content={"msg": "Param code is required", "code": 0}
        )

    # 根据代码获取股票信息
    stock = get_stock(code)
    # 检查股票信息是否找到
    if stock is None:
        return JSONResponse(
            status_code=404,
            content={"msg": f'Stock {code} info not found', "code": 0}
        )

    analyze_stock(stock)

    return {'code': 0, 'data': stock, 'msg': 'success'}


@analysis_router.get('/funds')
async def analysis_funds(db: Session = Depends(get_db),
                         exchange: str = None):
    # 从请求参数中获取股票指数代码
    # 检查是否提供了code参数
    if exchange is None:
        # 如果没有提供code参数，返回错误信息和400状态码
        return JSONResponse(
            status_code=400,
            content={'msg': 'Param exchange is required'}
        )

    index = None
    if exchange == 'SSE' or exchange == 'SZSE':
        index = '000001.SH'

    exec_analyze_funds = True
    if index is not None:
        # 根据代码获取股票信息
        stock = get_stock(index)
        # 检查股票信息是否找到
        if stock is None:
            return JSONResponse(
                status_code=404,
                content={'msg': 'Stock not found'}
            )

        strategy = analyze_stock(stock)
        if strategy is None or strategy.signal != 1:
            exec_analyze_funds = False

    if not exec_analyze_funds:
        return JSONResponse(
            status_code=200,
            content={'code': 0, 'msg': 'Index pattern not match, analysis_funds_task not run.'}
        )

    thread = threading.Thread(target=analysis_funds_task, args=(exchange, db))
    thread.start()

    # 返回任务id和200状态码
    return JSONResponse(
        status_code=200,
        content={'code': 0, 'msg': 'Job running'}
    )


def analysis_funds_task(exchange, db: Session):
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
    save_analyzed_stocks(stocks, db)

    generate_strategies(stocks, db)

    logger.info("🚀 分析基金ETF完成!!!")

    # 返回分析后的股票列表
    return stocks


class GetAnalyzedStocksReqBody(BaseModel):
    exchange: str = None
    code: str = None


@analysis_router.post('/analyzed')
async def get_analyzed_stocks(page: int | None = 1, page_size: int | None = 10,
                              req_body: GetAnalyzedStocksReqBody | None = None,
                              db: Session = Depends(get_db)):
    try:
        exchange = req_body.exchange if req_body else None
        code = req_body.code if req_body else None
        page = get_page_analyzed_stocks(db, exchange, code, page, page_size)
        return {"code": 0, 'data': page, "msg": "success"}
    except Exception as e:
        logger.info(e, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
