"""
Flask-SQLAlchemy数据库连接管理
"""
from flask_sqlalchemy import SQLAlchemy

# 创建SQLAlchemy实例
db = SQLAlchemy()


def init_db(app):
    """初始化数据库"""
    db.init_app(app)

    with app.app_context():
        # 导入所有模型
        from app.models import game, player, product, finance

        # 创建所有表（开发阶段使用，生产环境应使用Flask-Migrate）
        # db.create_all()
        pass

    return db
