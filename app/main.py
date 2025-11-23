"""
Flask 应用
"""
from flask import Flask, jsonify
from flask_cors import CORS
from app.core.config import config
from app.core.database import db, init_db
from app.services.session_cleanup import start_inactive_player_cleanup


def create_app(config_name='default', config_overrides=None):
    """创建Flask应用工厂"""
    app = Flask(__name__)

    # 载入配置
    app.config.from_object(config[config_name])
    if config_overrides:
        # 允许测试/脚本覆盖配置（如内存数据库）
        app.config.update(config_overrides)

    # 初始化CORS - 默认放开前端调试
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Session-Token"],
            "supports_credentials": False
        }
    })

    # 初始化数据库
    init_db(app)

    # 注册蓝图
    from app.api.v1 import game_bp, player_bp, production_bp, round_bp, finance_bp, shop_bp, employee_bp, product_bp, market_bp, auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(game_bp, url_prefix='/api/v1/games')
    app.register_blueprint(player_bp, url_prefix='/api/v1/players')
    app.register_blueprint(production_bp, url_prefix='/api/v1/production')
    app.register_blueprint(round_bp, url_prefix='/api/v1/rounds')
    app.register_blueprint(finance_bp, url_prefix='/api/v1/finance')
    app.register_blueprint(shop_bp, url_prefix='/api/v1/shops')
    app.register_blueprint(employee_bp, url_prefix='/api/v1/employees')
    app.register_blueprint(product_bp, url_prefix='/api/v1/products')
    app.register_blueprint(market_bp, url_prefix='/api/v1/market')

    # 启动自动清理任务（测试环境不启动，避免线程干扰内存数据库）
    if not app.config.get('TESTING'):
        start_inactive_player_cleanup(app)

    # 根路由
    @app.route('/')
    def index():
        return jsonify({
            "message": "欢迎使用奶茶大战API",
            "version": "1.0.0",
            "framework": "Flask",
            "endpoints": {
                "games": "/api/v1/games",
                "players": "/api/v1/players",
                "production": "/api/v1/production",
                "rounds": "/api/v1/rounds",
                "finance": "/api/v1/finance",
                "shops": "/api/v1/shops",
                "employees": "/api/v1/employees",
                "products": "/api/v1/products",
                "market": "/api/v1/market"
            }
        })

    # 健康检查
    @app.route('/health')
    def health():
        return jsonify({"status": "ok", "message": "Service is running"})

    return app


# 应用实例
app = create_app()


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=8000,
        debug=True
    )
