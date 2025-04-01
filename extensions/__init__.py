from flask_executor import Executor
from flask_redis import FlaskRedis
from flask_sqlalchemy import SQLAlchemy

executor = Executor()
db = SQLAlchemy()
redis_client = FlaskRedis()
