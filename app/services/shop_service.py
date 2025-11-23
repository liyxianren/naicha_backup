"""
Shop service
Handles shop opening, decoration, and management
"""
from typing import Dict
from app.core.database import db
from app.models.player import Player, Shop
from app.utils.game_constants import GameConstants


class ShopService:
    """Shop management service"""

    @staticmethod
    def open_shop(player_id: int, location: str, rent: float, round_number: int) -> Shop:
        """
        Open a new shop

        Args:
            player_id: Player ID
            location: Shop location
            rent: Monthly rent
            round_number: Round number when shop is opened

        Returns:
            Shop object

        Raises:
            ValueError: If player already has a shop or validation errors
        """
        player = Player.query.get(player_id)
        if not player:
            raise ValueError(f"Player {player_id} not found")

        # Check if player already has a shop
        if player.shop:
            raise ValueError(f"Player already has a shop at {player.shop.location}")

        # Validate rent
        if rent <= 0:
            raise ValueError("Rent must be positive")

        # Create shop with initial decoration level 0
        shop = Shop(
            player_id=player_id,
            location=location,
            rent=rent,
            decoration_level=0,
            max_employees=0,
            created_round=round_number
        )

        db.session.add(shop)
        db.session.commit()

        return shop

    @staticmethod
    def upgrade_decoration(player_id: int, target_level: int) -> Dict:
        """
        Upgrade shop decoration level

        Decoration costs and benefits:
        - Level 1: 400, max 2 employees
        - Level 2: 800, max 3 employees
        - Level 3: 1600, max 4 employees

        Args:
            player_id: Player ID
            target_level: Target decoration level (1-3)

        Returns:
            {
                "success": True,
                "previous_level": 0,
                "new_level": 1,
                "cost": 400,
                "max_employees": 2,
                "remaining_cash": 9600.0
            }

        Raises:
            ValueError: Various validation errors
        """
        player = Player.query.get(player_id)
        if not player:
            raise ValueError(f"Player {player_id} not found")

        if not player.shop:
            raise ValueError("Player doesn't have a shop yet")

        # Validate target level
        if target_level not in [1, 2, 3]:
            raise ValueError("Decoration level must be 1, 2, or 3")

        current_level = player.shop.decoration_level

        # Cannot downgrade
        if target_level <= current_level:
            raise ValueError(f"Cannot downgrade decoration. Current level: {current_level}")

        # Calculate cost
        cost = GameConstants.DECORATION_COSTS.get(target_level, 0)
        if cost <= 0:
            raise ValueError(f"Invalid decoration level: {target_level}")

        # Check cash
        if player.cash < cost:
            raise ValueError(
                f"Insufficient cash! Need {cost}, have {float(player.cash)}"
            )

        # Deduct cost
        player.cash -= cost

        # Update decoration
        previous_level = current_level
        player.shop.decoration_level = target_level
        player.shop.max_employees = GameConstants.MAX_EMPLOYEES.get(target_level, 0)

        db.session.commit()

        # Return the updated shop info
        return ShopService.get_shop_info(player_id)

    @staticmethod
    def get_shop_info(player_id: int) -> Dict:
        """
        Get shop information

        Args:
            player_id: Player ID

        Returns:
            Shop information dictionary

        Raises:
            ValueError: If player doesn't have a shop
        """
        player = Player.query.get(player_id)
        if not player:
            raise ValueError(f"Player {player_id} not found")

        if not player.shop:
            raise ValueError("Player doesn't have a shop yet")

        from app.models.player import Employee

        # Get employees
        employees = Employee.query.filter_by(
            shop_id=player.shop.id,
            is_active=True
        ).all()

        # Calculate total productivity and salary
        total_productivity = sum(emp.productivity for emp in employees)
        total_salary = sum(float(emp.salary) for emp in employees)

        return {
            "id": player.shop.id,
            "player_id": player_id,
            "location": player.shop.location,
            "rent": float(player.shop.rent),
            "decoration_level": player.shop.decoration_level,
            "max_employees": player.shop.max_employees,
            "created_round": player.shop.created_round,
            "employees": {
                "count": len(employees),
                "max": player.shop.max_employees,
                "total_productivity": total_productivity,
                "total_salary": total_salary,
                "list": [emp.to_dict() for emp in employees]
            }
        }

    @staticmethod
    def get_decoration_costs() -> Dict:
        """
        Get decoration costs and benefits for all levels

        Returns:
            {
                "1": {"cost": 400, "max_employees": 2},
                "2": {"cost": 800, "max_employees": 3},
                "3": {"cost": 1600, "max_employees": 4}
            }
        """
        return {
            str(level): {
                "cost": GameConstants.DECORATION_COSTS.get(level, 0),
                "max_employees": GameConstants.MAX_EMPLOYEES.get(level, 0)
            }
            for level in [1, 2, 3]
        }

    @staticmethod
    def close_shop(player_id: int) -> Dict:
        """
        Close a shop (admin/debug use)

        Args:
            player_id: Player ID

        Returns:
            {"success": True, "message": "Shop closed"}

        Raises:
            ValueError: If player doesn't have a shop
        """
        player = Player.query.get(player_id)
        if not player:
            raise ValueError(f"Player {player_id} not found")

        if not player.shop:
            raise ValueError("Player doesn't have a shop")

        # Delete shop (cascade will delete employees)
        db.session.delete(player.shop)
        db.session.commit()

        return {
            "success": True,
            "message": "Shop closed successfully"
        }


# Export
__all__ = ['ShopService']
