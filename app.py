import atexit
from threading import Lock

from flask import Flask, jsonify

from service_registry import register_service_with_consul, deregister_service_with_consul

app = Flask(__name__)
g_lock = Lock()
exit_handled = False


@app.route('/actuator/health', methods=['GET'])
def health():
    return jsonify({'status': 'UP'}), 200


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


# 注册退出处理函数
atexit.register(handle_at_exit, g_lock)

if __name__ == '__main__':
    try:
        register_service_with_consul()
        app.run()
    except Exception as e:
        print(f"Failed to start or register service: {e}")
