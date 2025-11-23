"""
Finance-related data models
Includes FinanceRecord, MaterialInventory, ResearchLog, MarketAction
"""
from app.core.database import db
from datetime import datetime


class FinanceRecord(db.Model):
    """Finance record model"""
    __tablename__ = "finance_records"

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id', ondelete='CASCADE'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)

    # Revenue
    total_revenue = db.Column(db.DECIMAL(10, 2), default=0.00)
    revenue_breakdown = db.Column(db.JSON, nullable=True, comment='Revenue details JSON')

    # Expenses
    rent_expense = db.Column(db.DECIMAL(8, 2), default=0.00, comment='Rent expense')
    salary_expense = db.Column(db.DECIMAL(8, 2), default=0.00, comment='Salary expense')
    material_expense = db.Column(db.DECIMAL(8, 2), default=0.00, comment='Material expense')
    decoration_expense = db.Column(db.DECIMAL(8, 2), default=0.00, comment='Decoration expense')
    research_expense = db.Column(db.DECIMAL(8, 2), default=0.00, comment='Market research expense')
    ad_expense = db.Column(db.DECIMAL(8, 2), default=0.00, comment='Advertisement expense')
    research_cost = db.Column(db.DECIMAL(8, 2), default=0.00, comment='Product research cost')
    total_expense = db.Column(db.DECIMAL(10, 2), default=0.00)

    # Profit
    round_profit = db.Column(db.DECIMAL(10, 2), default=0.00, comment='Current round profit')
    cumulative_profit = db.Column(db.DECIMAL(10, 2), default=0.00, comment='Cumulative profit')

    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    # Relationships
    player = db.relationship("Player", back_populates="finance_records")

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "player_id": self.player_id,
            "round_number": self.round_number,
            "revenue": {
                "total": float(self.total_revenue),
                "breakdown": self.revenue_breakdown
            },
            "expenses": {
                "rent": float(self.rent_expense),
                "salary": float(self.salary_expense),
                "material": float(self.material_expense),
                "decoration": float(self.decoration_expense),
                "market_research": float(self.research_expense),
                "advertisement": float(self.ad_expense),
                "product_research": float(self.research_cost),
                "total": float(self.total_expense)
            },
            "profit": {
                "round": float(self.round_profit),
                "cumulative": float(self.cumulative_profit)
            },
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class MaterialInventory(db.Model):
    """Material inventory model"""
    __tablename__ = "material_inventories"

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id', ondelete='CASCADE'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    material_type = db.Column(db.String(20), nullable=False, comment='tea, milk, fruit, ingredient')
    quantity = db.Column(db.Integer, default=0)
    purchase_price = db.Column(db.DECIMAL(8, 2), nullable=True, comment='Purchase unit price')

    # Relationships
    player = db.relationship("Player", back_populates="material_inventories")

    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('player_id', 'round_number', 'material_type',
                          name='uk_player_round_material'),
        db.Index('idx_player_round', 'player_id', 'round_number'),
    )

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "player_id": self.player_id,
            "round_number": self.round_number,
            "material_type": self.material_type,
            "quantity": self.quantity,
            "purchase_price": float(self.purchase_price) if self.purchase_price else None
        }


class ResearchLog(db.Model):
    """Research log model"""
    __tablename__ = "research_logs"

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id', ondelete='CASCADE'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('product_recipes.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    dice_result = db.Column(db.Integer, nullable=False, comment='Dice roll result')
    success = db.Column(db.Boolean, nullable=False, comment='Research success')
    cost = db.Column(db.DECIMAL(8, 2), default=600.00)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    # Relationships
    player = db.relationship("Player", back_populates="research_logs")
    recipe = db.relationship("ProductRecipe")

    # Index
    __table_args__ = (
        db.Index('idx_research_player_round', 'player_id', 'round_number'),
    )

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "player_id": self.player_id,
            "recipe_id": self.recipe_id,
            "recipe_name": self.recipe.name if self.recipe else None,
            "round_number": self.round_number,
            "dice_result": self.dice_result,
            "success": self.success,
            "cost": float(self.cost),
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class MarketAction(db.Model):
    """Market action model (advertisement, market research)"""
    __tablename__ = "market_actions"

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id', ondelete='CASCADE'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    action_type = db.Column(db.String(20), nullable=False, comment='ad (advertisement), research (market research)')
    cost = db.Column(db.DECIMAL(8, 2), nullable=False)
    result_value = db.Column(db.Integer, nullable=True, comment='Result value (ad score, etc.)')
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    # Relationships
    player = db.relationship("Player", back_populates="market_actions")

    # Index
    __table_args__ = (
        db.Index('idx_market_action_player_round', 'player_id', 'round_number'),
    )

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "player_id": self.player_id,
            "round_number": self.round_number,
            "action_type": self.action_type,
            "cost": float(self.cost),
            "result_value": self.result_value,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# Export models
__all__ = ['FinanceRecord', 'MaterialInventory', 'ResearchLog', 'MarketAction']
