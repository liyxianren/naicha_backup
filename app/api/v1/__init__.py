# API v1 Blueprints
from app.api.v1.auth import auth_bp
from app.api.v1.game import game_bp
from app.api.v1.player import player_bp
from app.api.v1.production import production_bp
from app.api.v1.round import round_bp
from app.api.v1.finance import finance_bp
from app.api.v1.shop import shop_bp
from app.api.v1.employee import employee_bp
from app.api.v1.product import product_bp
from app.api.v1.market import market_bp

__all__ = ['auth_bp', 'game_bp', 'player_bp', 'production_bp', 'round_bp', 'finance_bp', 'shop_bp', 'employee_bp', 'product_bp', 'market_bp']
