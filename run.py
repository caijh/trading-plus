import atexit
import os
import threading
from threading import Lock

from app import create_app
from extensions import db, scheduler
from registry.service_registry import register_service_with_consul, deregister_service_with_consul
from strategy.task import generate_strategy_task

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

g_lock = Lock()
exit_handled = False


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


def run_generate_strategy():
    """Wrapper function to ensure app context is available"""
    with app.app_context():
        generate_strategy_task()


def load_start_job():
    scheduler.add_job("generate_strategy_task", run_generate_strategy, trigger="cron", hour=22, minute=0)
    scheduler.start()


if __name__ == '__main__':
    try:
        app = create_app()

        with app.app_context():
            db.create_all()

        # 注册服务实例
        register_service_with_consul()
        # 注册退出处理函数
        atexit.register(handle_at_exit, g_lock)
        threading.Thread(target=load_start_job, daemon=True).start()  # 🔥 启动后台任务
        app.run(host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"Start App failed: {e}")
