from flask import Flask, json

from actuator import create_blueprint as actuator_blueprint
from analysis import create_blueprint as analysis_blueprint
from environment.service import env_vars
from extensions import executor, db, scheduler
from extensions import redis_client
from strategy import create_blueprint as strategy_blueprint


def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = env_vars.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = env_vars.SQLALCHEMY_TRACK_MODIFICATIONS
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "json_serializer": lambda obj: json.dumps(obj, ensure_ascii=False),
    }
    app.config['REDIS_URL'] = env_vars.get_redis_url()
    app.config["JSON_AS_ASCII"] = False

    executor.init_app(app)

    scheduler.init_app(app)

    db.init_app(app)

    redis_client.init_app(app)

    app.register_blueprint(actuator_blueprint())
    app.register_blueprint(analysis_blueprint())
    app.register_blueprint(strategy_blueprint())

    return app
