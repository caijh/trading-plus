# 加载 .env 文件
import os

from dotenv import load_dotenv

load_dotenv()

APPLICATION_NAME = os.getenv('APPLICATION_NAME', 'trading-plus')

# Consul配置
CONSUL_HOST = os.getenv('APPLICATION_CLOUD_DISCOVERY_SERVER_HOST', '127.0.0.1')  # Consul服务地址
CONSUL_PORT = int(os.getenv('APPLICATION_CLOUD_DISCOVERY_SERVER_PORT', 8500))  # Consul服务端口
CONSUL_TOKEN = os.getenv('APPLICATION_CLOUD_DISCOVERY_SERVER_TOKEN', None)

# Service配置
SERVICE_NAME = APPLICATION_NAME  # 服务名称
SERVICE_HOST = os.getenv('APPLICATION_CLOUD_DISCOVERY_HOST_IP', '127.0.0.1')
SERVICE_PORT = int(os.getenv('APPLICATION_CLOUD_DISCOVERY_HOST_PORT', '5000'))  # FastAPI服务的端口

# 数据库
DATABASE_URL = os.getenv('DATABASE_URL', None)

REDIS_HOST = os.getenv('REDIS_HOST', '127.0.0.1')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_USER = os.getenv('REDIS_USER', 'default')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
REDIS_DB = int(os.getenv('REDIS_DB', '0'))
REDIS_SSL = os.getenv('REDIS_SSL', False)

TRADING_DATA_URL = os.getenv('TRADING_DATA_URL', 'http://127.0.0.1:8080')

MIN_PROFIT_RATE = float(os.getenv('MIN_PROFIT_RATE', 1.5))
STRATEGY_RETENTION_DAY = int(os.getenv('STRATEGY_RETENTION_DAY', 5))
