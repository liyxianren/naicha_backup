"""
玩家相关数据模型 (Flask-SQLAlchemy)
"""
from app.core.database import db
from datetime import datetime


class Player(db.Model):
    """玩家模型"""
    __tablename__ = "players"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    nickname = db.Column(db.String(50), nullable=False)
    player_number = db.Column(db.Integer, nullable=False)
    turn_order = db.Column(db.Integer, default=0, comment='回合顺序，从0开始')
    cash = db.Column(db.DECIMAL(10, 2), default=10000.00)
    total_profit = db.Column(db.DECIMAL(10, 2), default=0.00)
    is_ready = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    joined_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    session_token = db.Column(db.String(100), unique=True, nullable=True, comment='玩家会话令牌，用于身份认证')
    last_active_at = db.Column(db.TIMESTAMP, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow, comment='最后活跃时间')

    # 关系
    game = db.relationship("Game", back_populates="players")
    shop = db.relationship("Shop", back_populates="player", uselist=False, cascade="all, delete-orphan")
    products = db.relationship("PlayerProduct", back_populates="player", cascade="all, delete-orphan")
    finance_records = db.relationship("FinanceRecord", back_populates="player", cascade="all, delete-orphan")
    material_inventories = db.relationship("MaterialInventory", back_populates="player", cascade="all, delete-orphan")
    research_logs = db.relationship("ResearchLog", back_populates="player", cascade="all, delete-orphan")
    market_actions = db.relationship("MarketAction", back_populates="player", cascade="all, delete-orphan")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "game_id": self.game_id,
            "name": self.nickname,  # 前端期望name字段
            "nickname": self.nickname,
            "player_number": self.player_number,
            "turn_order": self.turn_order if hasattr(self, 'turn_order') else 0,
            "cash": float(self.cash),
            "total_profit": float(self.total_profit),
            "is_ready": self.is_ready,
            "status": "active" if self.is_active else "bankrupt"
        }


class Shop(db.Model):
    """店铺模型"""
    __tablename__ = "shops"

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id", ondelete="CASCADE"), nullable=False, unique=True)
    location = db.Column(db.String(50), nullable=True)
    rent = db.Column(db.DECIMAL(8, 2), nullable=True)
    decoration_level = db.Column(db.Integer, default=0)
    max_employees = db.Column(db.Integer, default=0)
    created_round = db.Column(db.Integer, nullable=False)

    # 关系
    player = db.relationship("Player", back_populates="shop")
    employees = db.relationship("Employee", back_populates="shop", cascade="all, delete-orphan")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "player_id": self.player_id,
            "location": self.location,
            "rent": float(self.rent) if self.rent else 0,
            "decoration_level": self.decoration_level,
            "max_employees": self.max_employees,
            "created_round": self.created_round
        }


class Employee(db.Model):
    """员工模型"""
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id", ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    salary = db.Column(db.DECIMAL(8, 2), nullable=False)
    productivity = db.Column(db.Integer, nullable=False)
    hired_round = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    # 关系
    shop = db.relationship("Shop", back_populates="employees")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "shop_id": self.shop_id,
            "name": self.name,
            "salary": float(self.salary),
            "productivity": self.productivity,
            "hired_round": self.hired_round,
            "is_active": self.is_active
        }
