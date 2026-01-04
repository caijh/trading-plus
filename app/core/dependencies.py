# 创建依赖来获取数据库会话
from app.core.database import SessionLocal
from app.core.logger import logger


def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.info(f"Error: {e}", e, exc_info=True)
        raise
    finally:
        db.close()
