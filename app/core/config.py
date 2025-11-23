"""
Flask配置管理模块
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """基础配置"""

    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'naicha-game-secret-key-2025')
    DEBUG = os.getenv('DEBUG', 'True') == 'True'

    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'mysql+pymysql://root:I51dXb3JY6vgM87uf2SBsQ9W4yKRhOt0@sfo1.clusters.zeabur.com:32206/zeabur'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = DEBUG
    SQLALCHEMY_ENGINE_OPTIONS = {
        # 连接空闲被数据库关闭时自动重连，避免 OperationalError (e3q8)
        "pool_pre_ping": True,
        # 周期性回收连接，防止长时间空闲后失效
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", 300))
    }

    # CORS配置
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173,http://localhost:5174,http://localhost:5175').split(',')

    # Redis配置
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # 游戏配置
    MAX_ROUNDS = int(os.getenv('MAX_ROUNDS', 10))
    MAX_PLAYERS = int(os.getenv('MAX_PLAYERS', 4))
    INITIAL_CASH = float(os.getenv('INITIAL_CASH', 10000))

    # SocketIO配置
    SOCKETIO_CORS_ALLOWED_ORIGINS = CORS_ORIGINS


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
