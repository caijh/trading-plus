import os

from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

class EnvVars:
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    APPLICATION_CLOUD_DISCOVERY_SERVER_ADDRESS = os.getenv('APPLICATION_CLOUD_DISCOVERY_SERVER_ADDRESS', '127.0.0.1:8500')
    APPLICATION_CLOUD_DISCOVERY_SERVER_TOKEN = os.getenv('APPLICATION_CLOUD_DISCOVERY_SERVER_TOKEN', None)
    APPLICATION_CLOUD_DISCOVERY_HOST_IP = os.getenv('APPLICATION_CLOUD_DISCOVERY_HOST_IP', '127.0.0.1')
    APPLICATION_CLOUD_DISCOVERY_HOST_PORT = os.getenv('APPLICATION_CLOUD_DISCOVERY_HOST_PORT', 5000)
    TRADING_DATA_URL = os.getenv('TRADING_DATA_URL', 'http://127.0.0.1:8080')


env_vars = EnvVars()
