from databases import Database
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

engine = create_engine(
    settings.sqlalchemy_string
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 异步数据库连接（可以用于异步数据库操作）
database = Database(settings.sqlalchemy_string)
