"""
Product API Blueprint
Handles product research and management endpoints
"""
from flask import Blueprint, request, jsonify
from app.services.product_service import ProductService
from app.models.player import Player
from app.models.product import ProductRecipe

product_bp = Blueprint('product', __name__)


@product_bp.route('/research', methods=['POST'])
def research_product():
    """
    Research a product (offline dice roll, player inputs result)

    Request body:
    {
        "player_id": 1,
        "recipe_id": 1,
        "round_number": 1,
        "dice_result": 5
    }

    Response:
    {
        "success": true,
        "data": {
            "dice_result": 5,
            "required_roll": 2,
            "research_success": true,
            "product_unlocked": true,
            "product_name": "Milk Tea",
            "difficulty": 1,
            "cost": 600,
            "remaining_cash": 9400.0
        }
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "Request body is required"}), 400

        player_id = data.get('player_id')
        recipe_id = data.get('recipe_id')
        round_number = data.get('round_number')
        dice_result = data.get('dice_result')

        if not player_id:
            return jsonify({"success": False, "error": "player_id is required"}), 400
        if not recipe_id:
            return jsonify({"success": False, "error": "recipe_id is required"}), 400
        if not round_number:
            return jsonify({"success": False, "error": "round_number is required"}), 400
        if dice_result is None:
            return jsonify({"success": False, "error": "dice_result is required"}), 400

        # Research product
        result = ProductService.research_product(player_id, recipe_id, round_number, dice_result)

        return jsonify({
            "success": True,
            "data": result
        }), 200

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


@product_bp.route('/unlock', methods=['POST'])
def unlock_product():
    """
    Unlock product directly (admin/debug use)

    Request body:
    {
        "player_id": 1,
        "recipe_id": 1
    }

    Response:
    {
        "success": true,
        "data": {
            "id": 1,
            "player_id": 1,
            "recipe_id": 1,
            "is_unlocked": true
        }
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "Request body is required"}), 400

        player_id = data.get('player_id')
        recipe_id = data.get('recipe_id')

        if not player_id:
            return jsonify({"success": False, "error": "player_id is required"}), 400
        if not recipe_id:
            return jsonify({"success": False, "error": "recipe_id is required"}), 400

        # Unlock product
        product = ProductService.unlock_product_directly(player_id, recipe_id)

        return jsonify({
            "success": True,
            "data": {
                "id": product.id,
                "player_id": product.player_id,
                "recipe_id": product.recipe_id,
                "is_unlocked": product.is_unlocked
            }
        }), 200

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


@product_bp.route('/player/<int:player_id>/unlocked', methods=['GET'])
def get_unlocked_products(player_id: int):
    """
    Get all unlocked products for a player

    Response:
    {
        "success": true,
        "data": [
            {
                "id": 1,
                "recipe_id": 1,
                "recipe_name": "Milk Tea",
                "recipe_json": {"tea": 1, "milk": 2},
                "base_fan_rate": 10,
                "current_ad_score": 0,
                "total_sold": 0,
                "is_unlocked": true
            },
            ...
        ]
    }
    """
    try:
        # Verify player exists
        player = Player.query.get(player_id)
        if not player:
            return jsonify({"success": False, "error": f"Player {player_id} not found"}), 404

        # Get unlocked products
        result = ProductService.get_unlocked_products(player_id)

        return jsonify({
            "success": True,
            "data": result
        }), 200

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


@product_bp.route('/recipes', methods=['GET'])
def get_all_recipes():
    """
    Get all product recipes

    Query parameters:
        player_id: Optional, if provided will include unlock status for this player

    Response:
    {
        "success": true,
        "data": [
            {
                "recipe_id": 1,
                "name": "Milk Tea",
                "recipe_json": {"tea": 1, "milk": 2},
                "base_fan_rate": 10,
                "is_unlocked": false,  # Only if player_id provided
                "research_cost": 600
            },
            ...
        ]
    }
    """
    try:
        player_id = request.args.get('player_id', type=int)

        if player_id:
            # Get recipes with unlock status for player
            result = ProductService.get_available_recipes(player_id)
        else:
            # Get all recipes without unlock status
            recipes = ProductRecipe.query.all()
            result = [
                {
                    "recipe_id": r.id,
                    "name": r.name,
                    "recipe_json": r.recipe_json,
                    "base_fan_rate": r.base_fan_rate
                }
                for r in recipes
            ]

        return jsonify({
            "success": True,
            "data": result
        }), 200

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


@product_bp.route('/player/<int:player_id>/research-history', methods=['GET'])
def get_research_history(player_id: int):
    """
    Get product research history for a player

    Response:
    {
        "success": true,
        "data": [
            {
                "id": 1,
                "player_id": 1,
                "recipe_id": 1,
                "recipe_name": "Milk Tea",
                "round_number": 1,
                "dice_result": 5,
                "success": true,
                "cost": 600.0,
                "created_at": "..."
            },
            ...
        ]
    }
    """
    try:
        # Verify player exists
        player = Player.query.get(player_id)
        if not player:
            return jsonify({"success": False, "error": f"Player {player_id} not found"}), 404

        # Get research history
        result = ProductService.get_research_history(player_id)

        return jsonify({
            "success": True,
            "data": result
        }), 200

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


@product_bp.route('/<int:product_id>/details', methods=['GET'])
def get_product_details(product_id: int):
    """
    Get detailed information about a specific player product

    Query parameters:
        player_id: Player ID (required)

    Response:
    {
        "success": true,
        "data": {
            "id": 1,
            "recipe_id": 1,
            "recipe_name": "Milk Tea",
            "recipe_json": {"tea": 1, "milk": 2},
            "base_fan_rate": 10,
            "is_unlocked": true,
            "current_ad_score": 0,
            "total_sold": 0,
            "reputation": 0.0
        }
    }
    """
    try:
        player_id = request.args.get('player_id', type=int)

        if not player_id:
            return jsonify({"success": False, "error": "player_id query parameter is required"}), 400

        # Get product details
        result = ProductService.get_product_details(player_id, product_id)

        return jsonify({
            "success": True,
            "data": result
        }), 200

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


# Export blueprint
__all__ = ['product_bp']
