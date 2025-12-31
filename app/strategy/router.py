import threading

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app.core.dependencies import get_db
from app.strategy.model import TradingStrategy
from app.strategy.service import run_generate_strategy

strategy_router = APIRouter()


@strategy_router.get('/check-strategy')
async def generate_next_check_history(db: Session = Depends(get_db)):
    thread = threading.Thread(target=run_generate_strategy, args=('', db))
    thread.start()
    return {'code': 0, 'msg': 'Job running'}


class GetAnalyzedStocksReqBody(BaseModel):
    exchange: str = None
    code: str = None


@strategy_router.post('/trading')
async def get_analyzed_stocks(page: int = 1, page_size: int = 10, req_body: GetAnalyzedStocksReqBody | None = None,
                              db: Session = Depends(get_db)):
    try:
        # 从请求体中获取 exchange 和 code 参数
        exchange = req_body.exchange if req_body else None
        code = req_body.code if req_body else None

        # 构建基础查询
        query = db.query(TradingStrategy).order_by(TradingStrategy.updated_at.desc())

        # 按 exchange 和 code 添加过滤条件（如果存在）
        if exchange:
            query = query.filter_by(exchange=exchange)
        if code:
            query = query.filter_by(code=code)

        # 计算 skip 和 limit
        skip = (page - 1) * page_size
        limit = page_size

        # 查询数据并分页
        items = query.offset(skip).limit(limit).all()
        total = query.count()  # 获取总记录数

        data = {
            "total": total,
            "page_num": (total + page_size - 1) // page_size,
            "page": page,
            "page_size": page_size,
            "has_next": page * page_size < total,
            "has_prev": page > 1,
            "items": [strategy.__dict__ for strategy in items]
        }

        # 返回格式化数据
        return {"code": 0, 'data': data, "msg": "success"}
    except Exception as e:
        print(e)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
