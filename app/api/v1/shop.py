"""
Shop API Blueprint
Handles shop management endpoints
"""
from flask import Blueprint, request, jsonify
from app.services.shop_service import ShopService
from app.models.player import Player

shop_bp = Blueprint('shop', __name__)


@shop_bp.route('/open', methods=['POST'])
def open_shop():
    """
    Open a new shop

    Request body:
    {
        "player_id": 1,
        "location": "Downtown",
        "rent": 500,
        "round_number": 1
    }

    Response:
    {
        "success": true,
        "data": {
            "id": 1,
            "player_id": 1,
            "location": "Downtown",
            "rent": 500.0,
            "decoration_level": 0,
            "max_employees": 0
        }
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "Request body is required"
            }), 400

        player_id = data.get('player_id')
        location = data.get('location')
        rent = data.get('rent')
        round_number = data.get('round_number')

        if not player_id:
            return jsonify({"success": False, "error": "player_id is required"}), 400
        if not location:
            return jsonify({"success": False, "error": "location is required"}), 400
        if rent is None:
            return jsonify({"success": False, "error": "rent is required"}), 400
        if not round_number:
            return jsonify({"success": False, "error": "round_number is required"}), 400

        # Open shop
        shop = ShopService.open_shop(player_id, location, rent, round_number)

        return jsonify({
            "success": True,
            "data": shop.to_dict()
        }), 201

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


@shop_bp.route('/<int:player_id>/upgrade', methods=['POST'])
def upgrade_decoration(player_id: int):
    """
    Upgrade shop decoration

    Request body:
    {
        "target_level": 1
    }

    Response:
    {
        "success": true,
        "data": {
            "previous_level": 0,
            "new_level": 1,
            "cost": 400,
            "max_employees": 2,
            "remaining_cash": 9600.0
        }
    }
    """
    try:
        data = request.get_json()
        print(f"[UPGRADE] player_id: {player_id}, data: {data}")

        if not data:
            return jsonify({"success": False, "error": "Request body is required"}), 400

        target_level = data.get('target_level')

        if target_level is None:
            return jsonify({"success": False, "error": "target_level is required"}), 400

        # Upgrade decoration
        result = ShopService.upgrade_decoration(player_id, target_level)
        print(f"[UPGRADE SUCCESS] result: {result}")

        return jsonify({
            "success": True,
            "data": result
        }), 200

    except ValueError as e:
        print(f"[UPGRADE ERROR] ValueError: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        print(f"[UPGRADE ERROR] Exception: {str(e)}")
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


@shop_bp.route('/<int:player_id>', methods=['GET'])
def get_shop_info(player_id: int):
    """
    Get shop information

    Response:
    {
        "success": true,
        "data": {
            "id": 1,
            "player_id": 1,
            "location": "Downtown",
            "rent": 500.0,
            "decoration_level": 1,
            "max_employees": 2,
            "employees": {
                "count": 1,
                "max": 2,
                "total_productivity": 5,
                "total_salary": 1000.0,
                "list": [...]
            }
        }
    }

    If player doesn't have a shop yet, returns:
    {
        "success": true,
        "data": null,
        "has_shop": false
    }
    """
    try:
        # Verify player exists
        player = Player.query.get(player_id)
        if not player:
            return jsonify({"success": False, "error": f"Player {player_id} not found"}), 404

        # Check if player has a shop
        if not player.shop:
            return jsonify({
                "success": True,
                "data": None,
                "has_shop": False,
                "message": "Player doesn't have a shop yet"
            }), 200

        # Get shop info
        result = ShopService.get_shop_info(player_id)

        return jsonify({
            "success": True,
            "data": result,
            "has_shop": True
        }), 200

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


@shop_bp.route('/decoration-costs', methods=['GET'])
def get_decoration_costs():
    """
    Get decoration costs for all levels

    Response:
    {
        "success": true,
        "data": {
            "1": {"cost": 400, "max_employees": 2},
            "2": {"cost": 800, "max_employees": 3},
            "3": {"cost": 1600, "max_employees": 4}
        }
    }
    """
    try:
        result = ShopService.get_decoration_costs()

        return jsonify({
            "success": True,
            "data": result
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


@shop_bp.route('/<int:player_id>/close', methods=['DELETE'])
def close_shop(player_id: int):
    """
    Close shop (admin/debug use)

    Response:
    {
        "success": true,
        "message": "Shop closed successfully"
    }
    """
    try:
        result = ShopService.close_shop(player_id)

        return jsonify(result), 200

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


# Export blueprint
__all__ = ['shop_bp']
