"""
Product service
Handles product research, unlocking, and management
"""
import random
from typing import Dict, List
from app.core.database import db
from app.models.player import Player
from app.models.product import ProductRecipe, PlayerProduct
from app.models.finance import ResearchLog
from app.utils.game_constants import GameConstants


class ProductService:
    """Product management service"""

    @staticmethod
    def research_product(player_id: int, recipe_id: int, round_number: int, dice_result: int) -> Dict:
        """
        Research a product (offline dice roll, player inputs result)

        Rules:
        - Cost: 600
        - Player rolls 1d6 offline and inputs result
        - Difficulty 3: need >= 2 (83% success) - 奶茶、椰奶、柠檬茶、果汁
        - Difficulty 4: need >= 3 (67% success) - 珍珠奶茶、水果奶昔
        - Difficulty 5: need >= 4 (50% success) - 水果茶
        - If successful, product is unlocked

        Args:
            player_id: Player ID
            recipe_id: Product recipe ID
            round_number: Current round number
            dice_result: Dice result from offline roll (1-6)

        Returns:
            {
                "success": True,
                "dice_result": 5,
                "required_roll": 2,
                "research_success": True,
                "product_unlocked": True,
                "product_name": "Milk Tea",
                "difficulty": 1,
                "cost": 600,
                "remaining_cash": 9400.0
            }

        Raises:
            ValueError: Various validation errors
        """
        player = Player.query.get(player_id)
        if not player:
            raise ValueError(f"Player {player_id} not found")

        # Check recipe exists
        recipe = ProductRecipe.query.get(recipe_id)
        if not recipe:
            raise ValueError(f"Product recipe {recipe_id} not found")

        # Validate dice result
        if dice_result < 1 or dice_result > 6:
            raise ValueError(f"Invalid dice result: {dice_result}. Must be between 1 and 6")

        # Check if already unlocked
        existing = PlayerProduct.query.filter_by(
            player_id=player_id,
            recipe_id=recipe_id
        ).first()

        if existing and existing.is_unlocked:
            raise ValueError(f"Product '{recipe.name}' is already unlocked")

        # Check cash
        cost = GameConstants.PRODUCT_RESEARCH_COST
        if player.cash < cost:
            raise ValueError(
                f"Insufficient cash! Need {cost}, have {float(player.cash)}"
            )

        # Deduct cost
        player.cash -= cost

        # Check against recipe difficulty
        # Difficulty 3: need >= 3 (easy) - 67% success rate (4,5,6成功)
        # Difficulty 4: need >= 4 (medium) - 50% success rate (4,5,6成功)
        # Difficulty 5: need >= 5 (hard) - 33% success rate (5,6成功)
        required_roll = recipe.difficulty
        research_success = dice_result >= required_roll

        # Create research log
        research_log = ResearchLog(
            player_id=player_id,
            recipe_id=recipe_id,
            round_number=round_number,
            dice_result=dice_result,
            success=research_success,
            cost=cost
        )
        db.session.add(research_log)

        # If successful, unlock product
        product_unlocked = False
        if research_success:
            if existing:
                # Update existing record
                existing.is_unlocked = True
                existing.unlocked_round = round_number
            else:
                # Create new player product
                player_product = PlayerProduct(
                    player_id=player_id,
                    recipe_id=recipe_id,
                    is_unlocked=True,
                    unlocked_round=round_number,
                    current_ad_score=0,
                    total_sold=0
                )
                db.session.add(player_product)

            product_unlocked = True

        db.session.commit()

        return {
            "success": True,
            "dice_result": dice_result,
            "required_roll": required_roll,
            "research_success": research_success,
            "product_unlocked": product_unlocked,
            "product_name": recipe.name,
            "difficulty": recipe.difficulty,
            "cost": cost,
            "remaining_cash": float(player.cash)
        }

    @staticmethod
    def unlock_product_directly(player_id: int, recipe_id: int) -> PlayerProduct:
        """
        Unlock product directly without research (admin/debug use)

        Args:
            player_id: Player ID
            recipe_id: Product recipe ID

        Returns:
            PlayerProduct object

        Raises:
            ValueError: If validation fails
        """
        player = Player.query.get(player_id)
        if not player:
            raise ValueError(f"Player {player_id} not found")

        recipe = ProductRecipe.query.get(recipe_id)
        if not recipe:
            raise ValueError(f"Product recipe {recipe_id} not found")

        # Check if already exists
        existing = PlayerProduct.query.filter_by(
            player_id=player_id,
            recipe_id=recipe_id
        ).first()

        if existing:
            existing.is_unlocked = True
            db.session.commit()
            return existing

        # Create new
        player_product = PlayerProduct(
            player_id=player_id,
            recipe_id=recipe_id,
            is_unlocked=True,
            current_ad_score=0,
            total_sold=0
        )

        db.session.add(player_product)
        db.session.commit()

        return player_product

    @staticmethod
    def get_unlocked_products(player_id: int) -> List[Dict]:
        """
        Get all unlocked products for a player

        Args:
            player_id: Player ID

        Returns:
            List of unlocked product dictionaries
        """
        player = Player.query.get(player_id)
        if not player:
            raise ValueError(f"Player {player_id} not found")

        products = PlayerProduct.query.filter_by(
            player_id=player_id,
            is_unlocked=True
        ).all()

        result = []
        for product in products:
            result.append({
                "id": product.id,
                "player_id": product.player_id,
                "recipe_id": product.recipe_id,
                "is_unlocked": product.is_unlocked,
                "current_ad_score": product.current_ad_score,
                "total_sold": product.total_sold,
                "current_price": product.current_price,
                "last_price_change_round": product.last_price_change_round,
                "recipe": {
                    "id": product.recipe.id,
                    "name": product.recipe.name,
                    "difficulty": product.recipe.difficulty,
                    "base_fan_rate": product.recipe.base_fan_rate,
                    "cost_per_unit": product.recipe.cost_per_unit,
                    "recipe_json": product.recipe.recipe_json,
                    "is_active": product.recipe.is_active
                }
            })

        return result

    @staticmethod
    def get_available_recipes(player_id: int) -> List[Dict]:
        """
        Get all product recipes that player can research

        Returns recipes that are:
        - Either not unlocked yet
        - Or unlocked but can be researched again

        Args:
            player_id: Player ID

        Returns:
            List of recipe dictionaries with unlock status
        """
        player = Player.query.get(player_id)
        if not player:
            raise ValueError(f"Player {player_id} not found")

        # Get all recipes
        all_recipes = ProductRecipe.query.all()

        # Get player's unlocked products
        unlocked_products = {
            p.recipe_id: p
            for p in PlayerProduct.query.filter_by(
                player_id=player_id,
                is_unlocked=True
            ).all()
        }

        result = []
        for recipe in all_recipes:
            is_unlocked = recipe.id in unlocked_products

            result.append({
                "recipe_id": recipe.id,
                "name": recipe.name,
                "recipe_json": recipe.recipe_json,
                "base_fan_rate": recipe.base_fan_rate,
                "difficulty": recipe.difficulty,  # 添加难度信息
                "is_unlocked": is_unlocked,
                "research_cost": GameConstants.PRODUCT_RESEARCH_COST
            })

        return result

    @staticmethod
    def get_research_history(player_id: int) -> List[Dict]:
        """
        Get product research history for a player

        Args:
            player_id: Player ID

        Returns:
            List of research log dictionaries
        """
        player = Player.query.get(player_id)
        if not player:
            raise ValueError(f"Player {player_id} not found")

        logs = ResearchLog.query.filter_by(player_id=player_id).order_by(
            ResearchLog.round_number.desc()
        ).all()

        return [log.to_dict() for log in logs]

    @staticmethod
    def get_product_details(player_id: int, product_id: int) -> Dict:
        """
        Get detailed information about a specific player product

        Args:
            player_id: Player ID
            product_id: PlayerProduct ID

        Returns:
            Product details dictionary

        Raises:
            ValueError: If product not found
        """
        product = PlayerProduct.query.get(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")

        if product.player_id != player_id:
            raise ValueError(f"Product {product_id} does not belong to player {player_id}")

        from app.services.calculation_engine import ReputationCalculator

        # Calculate reputation
        reputation = ReputationCalculator.calculate(product)

        return {
            "id": product.id,
            "recipe_id": product.recipe_id,
            "recipe_name": product.recipe.name,
            "recipe_json": product.recipe.recipe_json,
            "base_fan_rate": product.recipe.base_fan_rate,
            "is_unlocked": product.is_unlocked,
            "current_ad_score": product.current_ad_score,
            "total_sold": product.total_sold,
            "reputation": reputation
        }


# Export
__all__ = ['ProductService']
