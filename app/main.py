import atexit
import os
from threading import Lock

from flask import Flask
from flask_redis import FlaskRedis

from actuator import actuator
from analysis import analysis
from env import env_vars
from service_registry import register_service_with_consul, deregister_service_with_consul

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

g_lock = Lock()
exit_handled = False

app = Flask(__name__)
app.config['REDIS_URL'] = env_vars.get_redis_url()

app.register_blueprint(actuator)
app.register_blueprint(analysis)

redis_client = FlaskRedis(app)

def handle_at_exit(lock):
    """处理退出事件"""
    global exit_handled

    # 加锁，确保只有一个线程可以执行注销逻辑
    with lock:
        if exit_handled:
            return  # 如果已经处理过，直接返回
        exit_handled = True  # 设置标志位
        print("Exiting...")
        deregister_service_with_consul()


if __name__ == '__main__':
    try:
        register_service_with_consul()
        # 注册退出处理函数
        atexit.register(handle_at_exit, g_lock)
        app.run(host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"Failed to start App: {e}")
