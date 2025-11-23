"""
产品相关数据模型 (Flask-SQLAlchemy)
"""
from app.core.database import db


class ProductRecipe(db.Model):
    """产品配方模型"""
    __tablename__ = "product_recipes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    difficulty = db.Column(db.Integer, nullable=False)
    base_fan_rate = db.Column(db.DECIMAL(5, 2), nullable=False)
    cost_per_unit = db.Column(db.DECIMAL(6, 2), nullable=False)
    recipe_json = db.Column(db.JSON, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    # 关系
    player_products = db.relationship("PlayerProduct", back_populates="recipe")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "difficulty": self.difficulty,
            "base_fan_rate": float(self.base_fan_rate),
            "cost_per_unit": float(self.cost_per_unit),
            "recipe_json": self.recipe_json,
            "is_active": self.is_active
        }


class PlayerProduct(db.Model):
    """玩家产品模型"""
    __tablename__ = "player_products"

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey("product_recipes.id"), nullable=False)
    is_unlocked = db.Column(db.Boolean, default=False)
    unlocked_round = db.Column(db.Integer, nullable=True)
    total_sold = db.Column(db.Integer, default=0)
    current_price = db.Column(db.DECIMAL(6, 2), nullable=True)
    current_ad_score = db.Column(db.Integer, default=0)
    last_price_change_round = db.Column(db.Integer, default=0, comment='Last round when price was changed')

    # 关系
    player = db.relationship("Player", back_populates="products")
    recipe = db.relationship("ProductRecipe", back_populates="player_products")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "player_id": self.player_id,
            "recipe_id": self.recipe_id,
            "is_unlocked": self.is_unlocked,
            "unlocked_round": self.unlocked_round,
            "total_sold": self.total_sold,
            "current_price": float(self.current_price) if self.current_price else None,
            "current_ad_score": self.current_ad_score,
            "recipe": self.recipe.to_dict() if self.recipe else None
        }


class RoundProduction(db.Model):
    """回合生产计划模型"""
    __tablename__ = "round_productions"

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, nullable=False)  # PlayerProduct.id
    allocated_productivity = db.Column(db.Integer, default=0)
    price = db.Column(db.DECIMAL(6, 2), nullable=True)
    produced_quantity = db.Column(db.Integer, default=0)
    sold_quantity = db.Column(db.Integer, default=0)
    sold_to_high_tier = db.Column(db.Integer, default=0)
    sold_to_low_tier = db.Column(db.Integer, default=0)
    revenue = db.Column(db.DECIMAL(10, 2), default=0.00)

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "player_id": self.player_id,
            "round_number": self.round_number,
            "product_id": self.product_id,
            "allocated_productivity": self.allocated_productivity,
            "price": float(self.price) if self.price else None,
            "produced_quantity": self.produced_quantity,
            "sold_quantity": self.sold_quantity,
            "sold_to_high_tier": self.sold_to_high_tier,
            "sold_to_low_tier": self.sold_to_low_tier,
            "revenue": float(self.revenue)
        }
