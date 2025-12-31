# 配置日志记录器
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(asctime)s - %(message)s")
logger = logging.getLogger(__name__)
