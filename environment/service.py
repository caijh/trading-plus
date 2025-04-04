import os

from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

class EnvVars:
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    APPLICATION_CLOUD_DISCOVERY_SERVER_HOST = os.getenv('APPLICATION_CLOUD_DISCOVERY_SERVER_HOST', '127.0.0.1')
    APPLICATION_CLOUD_DISCOVERY_SERVER_PORT = os.getenv('APPLICATION_CLOUD_DISCOVERY_SERVER_PORT', 8500)
    APPLICATION_CLOUD_DISCOVERY_SERVER_TOKEN = os.getenv('APPLICATION_CLOUD_DISCOVERY_SERVER_TOKEN', None)
    APPLICATION_CLOUD_DISCOVERY_HOST_IP = os.getenv('APPLICATION_CLOUD_DISCOVERY_HOST_IP', '127.0.0.1')
    APPLICATION_CLOUD_DISCOVERY_HOST_PORT = os.getenv('APPLICATION_CLOUD_DISCOVERY_HOST_PORT', 5000)
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/mydatabase")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TRADING_DATA_URL = os.getenv('TRADING_DATA_URL', 'http://127.0.0.1:8080')
    REDIS_HOST = os.getenv('REDIS_HOST', '127.0.0.1')
    REDIS_PORT = os.getenv('REDIS_PORT', 6379)
    REDIS_USER = os.getenv('REDIS_USER', 'default')
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
    REDIS_DB = os.getenv('REDIS_DB', 0)
    REDIS_SSL = os.getenv('REDIS_SSL', 'False').lower() == 'true'

    def get_redis_url(self):
        protocol = 'redis'
        if self.REDIS_SSL:
            protocol = 'rediss'
        if self.REDIS_PASSWORD is None:
            return f'{protocol}://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}'
        else:
            return f'{protocol}://{self.REDIS_USER}:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}'


env_vars = EnvVars()
