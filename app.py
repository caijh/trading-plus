from flask import Flask

from actuator import create_blueprint as actuator_blueprint
from analysis import create_blueprint as analysis_blueprint
from environment.env import env_vars
from extensions import executor, db
from extensions import redis_client


def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = env_vars.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = env_vars.SQLALCHEMY_TRACK_MODIFICATIONS
    app.config['REDIS_URL'] = env_vars.get_redis_url()

    executor.init_app(app)

    db.init_app(app)

    redis_client.init_app(app)

    app.register_blueprint(actuator_blueprint())
    app.register_blueprint(analysis_blueprint())
    return app
