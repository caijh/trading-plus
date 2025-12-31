from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app.analysis.router import analysis_router
from app.core.database import Base, engine
from app.core.env import DATABASE_URL
from app.core.middleware import ClientInfoMiddleware
from app.core.redis import test_redis_connection
from app.core.registry import register_service, deregister_service, actuator_router
from app.strategy.router import strategy_router


# 使用 Lifespan 事件进行启动和关闭操作
@asynccontextmanager
async def lifespan(_app: FastAPI):
    # 测试 Redis 连接是否正常
    if not test_redis_connection():
        raise HTTPException(status_code=500, detail="Redis connection failed")

    # 启动时注册到 Consul
    await register_service()

    # 结束时注销服务
    yield

    await deregister_service()


app = FastAPI(lifespan=lifespan)

app.add_middleware(ClientInfoMiddleware)

# 创建数据库表（如果没有的话）
if DATABASE_URL is not None:  # 仅在有数据库 URL 的时候创建表
    Base.metadata.create_all(bind=engine)

app.include_router(router=actuator_router, prefix='/actuator', tags=['actuator'])
app.include_router(router=analysis_router, prefix='/analysis', tags=['analysis'])
app.include_router(router=strategy_router, prefix='/strategy', tags=['strategy'])


@app.get("/")
async def greet_json():
    return {"Hello": "World!"}
