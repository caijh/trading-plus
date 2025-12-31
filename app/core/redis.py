import redis
from fastapi import HTTPException

from app.core.env import REDIS_HOST, REDIS_PORT, REDIS_USER, REDIS_PASSWORD

# 创建 Redis 连接池
redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT,
                                 username=REDIS_USER, password=REDIS_PASSWORD,
                                 db=0, decode_responses=True)


# 测试 Redis 连接
def test_redis_connection():
    try:
        redis_client.ping()  # 发送 Ping 请求测试 Redis 连接
        return True
    except redis.ConnectionError:
        raise HTTPException(status_code=500, detail="Could not connect to Redis")


# 获取缓存
def get_cache(key: str):
    try:
        value = redis_client.get(key)
        return value
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error getting data from Redis")


# 设置缓存
def set_cache(key: str, value: str, ttl: int = 3600):  # ttl in seconds
    try:
        redis_client.setex(key, ttl, value)  # 设置缓存并指定过期时间
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error setting data to Redis")


# 删除缓存
def delete_cache(key: str):
    try:
        redis_client.delete(key)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error deleting data from Redis")
