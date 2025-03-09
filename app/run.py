import atexit
from threading import Lock

from flask import Flask, jsonify, request

from index import analyze_index, analyze_index_stocks
from service_registry import register_service_with_consul, deregister_service_with_consul
from stock import get_stock, analyze_stock

app = Flask(__name__)
g_lock = Lock()
exit_handled = False


@app.route('/actuator/health', methods=['GET'])
def health():
    return jsonify({'status': 'UP'}), 200


@app.route('/analysis/index', methods=['GET'])
def analysis_index_stocks():
    indexes = analyze_index()
    return jsonify(indexes), 200


@app.route('/analysis/index/stock', methods=['GET'])
def analysis_index():
    code = request.args.get('code')
    if code is None:
        return jsonify({'message': 'param code is required'}), 400

    stocks = analyze_index_stocks(code)
    return jsonify(stocks), 200


@app.route('/analysis/stock', methods=['GET'])
def analysis_stock():
    code = request.args.get('code')
    if code is None:
        return jsonify({'message': 'param code is required'}), 400

    stock = get_stock(code)
    if stock is None:
        return jsonify({'message': 'stock not found'}), 404

    analyze_stock(stock)
    return jsonify(stock), 200


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
