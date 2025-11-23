"""
游戏相关数据模型 (Flask-SQLAlchemy)
"""
from app.core.database import db
from datetime import datetime


class Game(db.Model):
    """游戏房间模型"""
    __tablename__ = "games"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True, comment='游戏房间名称')
    room_code = db.Column(db.String(6), unique=True, nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default='waiting')
    current_round = db.Column(db.Integer, default=1)
    max_players = db.Column(db.Integer, default=4)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    started_at = db.Column(db.TIMESTAMP, nullable=True)
    finished_at = db.Column(db.TIMESTAMP, nullable=True)
    settings = db.Column(db.JSON, nullable=True)

    # 关系
    players = db.relationship("Player", back_populates="game", cascade="all, delete-orphan")
    customer_flows = db.relationship("CustomerFlow", back_populates="game", cascade="all, delete-orphan")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name if self.name else self.room_code,  # 优先使用名称，否则使用房间号
            "room_code": self.room_code,
            "status": self.status,
            "current_round": self.current_round,
            "max_players": self.max_players,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None
        }


class CustomerFlow(db.Model):
    """客流量模型"""
    __tablename__ = "customer_flows"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    high_tier_customers = db.Column(db.Integer, nullable=False)
    low_tier_customers = db.Column(db.Integer, nullable=False)
    generated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    # 关系
    game = db.relationship("Game", back_populates="customer_flows")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "game_id": self.game_id,
            "round_number": self.round_number,
            "high_tier_customers": self.high_tier_customers,
            "low_tier_customers": self.low_tier_customers
        }
