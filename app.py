from flask import Flask

from actuator import create_blueprint as actuator_blueprint
from analysis import create_blueprint as analysis_blueprint
from environment.env import env_vars
from extensions import executor
from extensions import redis_client


def create_app():
    app = Flask(__name__)

    app.register_blueprint(actuator_blueprint())
    app.register_blueprint(analysis_blueprint())

    app.config['REDIS_URL'] = env_vars.get_redis_url()
    redis_client.init_app(app)

    executor.init_app(app)

    return app
