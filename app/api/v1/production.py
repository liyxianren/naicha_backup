"""
Production API Blueprint
Handles production plan submission and queries
"""
from flask import Blueprint, request, jsonify
from app.services.production_service import ProductionService
from app.models.player import Player
from app.models.game import Game

production_bp = Blueprint('production', __name__)


@production_bp.route('/submit', methods=['POST'])
def submit_production_plan():
    """
    Submit production plan for a player in a specific round

    Request body:
    {
        "player_id": 1,
        "round_number": 1,
        "productions": [
            {"product_id": 1, "productivity": 5, "price": 15},
            {"product_id": 2, "productivity": 10, "price": 25}
        ]
    }

    Response:
    {
        "success": true,
        "data": {
            "material_needs": {"tea": 10, "milk": 20, ...},
            "material_costs": {
                "tea": {"quantity": 10, "unit_price": 5.4, "total": 54.0},
                ...
                "total_cost": 123.45
            },
            "remaining_cash": 8876.55
        }
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        if not data:
            return jsonify({
                "success": False,
                "error": "Request body is required"
            }), 400

        player_id = data.get('player_id')
        round_number = data.get('round_number')
        productions = data.get('productions', [])

        if not player_id:
            return jsonify({
                "success": False,
                "error": "player_id is required"
            }), 400

        if not round_number:
            return jsonify({
                "success": False,
                "error": "round_number is required"
            }), 400

        if not isinstance(productions, list):
            return jsonify({
                "success": False,
                "error": "productions must be a list"
            }), 400

        # Verify player exists and is active
        player = Player.query.get(player_id)
        if not player:
            return jsonify({
                "success": False,
                "error": f"Player {player_id} not found"
            }), 404

        if not player.is_active:
            return jsonify({
                "success": False,
                "error": "Player is not active"
            }), 400

        # Verify game is in progress
        game = Game.query.get(player.game_id)
        if not game:
            return jsonify({
                "success": False,
                "error": "Game not found"
            }), 404

        if game.status != 'in_progress':
            return jsonify({
                "success": False,
                "error": f"Game is not in progress (current status: {game.status})"
            }), 400

        # Verify round number matches current game round
        if round_number != game.current_round:
            return jsonify({
                "success": False,
                "error": f"Round number mismatch. Game is at round {game.current_round}, but you submitted for round {round_number}"
            }), 400

        # Call service to submit production plan
        result = ProductionService.submit_production_plan(
            player_id=player_id,
            round_number=round_number,
            productions=productions
        )

        # Check if all players have submitted their production plans
        all_submitted = True
        players = Player.query.filter_by(game_id=game.id, is_active=True).all()
        for p in players:
            from app.models.product import RoundProduction
            productions_check = RoundProduction.query.filter_by(
                player_id=p.id,
                round_number=round_number
            ).all()
            if not productions_check:
                all_submitted = False
                break

        result["all_players_submitted"] = all_submitted

        return jsonify({
            "success": True,
            "data": result
        }), 200

    except ValueError as e:
        # Validation errors from service layer
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

    except Exception as e:
        # Unexpected errors
        import traceback
        error_traceback = traceback.format_exc()
        print(f"=== PRODUCTION SUBMIT ERROR ===")
        print(error_traceback)
        print(f"=== END ERROR ===")
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}",
            "traceback": error_traceback
        }), 500


@production_bp.route('/<int:player_id>/<int:round_number>', methods=['GET'])
def get_production_plan(player_id: int, round_number: int):
    """
    Get production plan for a player in a specific round

    URL parameters:
        player_id: Player ID
        round_number: Round number

    Response:
    {
        "success": true,
        "data": [
            {
                "id": 1,
                "product_id": 1,
                "product_name": "Milk Tea",
                "allocated_productivity": 5,
                "price": 15.0,
                "produced_quantity": 5,
                "sold_quantity": 3,
                "sold_to_high_tier": 2,
                "sold_to_low_tier": 1,
                "revenue": 45.0
            },
            ...
        ]
    }
    """
    try:
        # Verify player exists
        player = Player.query.get(player_id)
        if not player:
            return jsonify({
                "success": False,
                "error": f"Player {player_id} not found"
            }), 404

        # Get production plan
        result = ProductionService.get_production_plan(
            player_id=player_id,
            round_number=round_number
        )

        return jsonify({
            "success": True,
            "data": result
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500


@production_bp.route('/material-preview', methods=['POST'])
def preview_material_needs():
    """
    Preview material needs and costs without submitting the plan

    Request body:
    {
        "productions": [
            {"product_id": 1, "productivity": 5, "price": 15},
            {"product_id": 2, "productivity": 10, "price": 25}
        ]
    }

    Response:
    {
        "success": true,
        "data": {
            "material_needs": {"tea": 10, "milk": 20, ...},
            "material_costs": {
                "tea": {"quantity": 10, "unit_price": 5.4, "total": 54.0},
                ...
                "total_cost": 123.45
            }
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

        productions = data.get('productions', [])

        if not isinstance(productions, list):
            return jsonify({
                "success": False,
                "error": "productions must be a list"
            }), 400

        # Calculate material needs
        from app.services.calculation_engine import DiscountCalculator

        material_needs = ProductionService.calculate_material_needs(productions)
        material_costs = DiscountCalculator.calculate_material_costs(material_needs)

        return jsonify({
            "success": True,
            "data": {
                "material_needs": material_needs,
                "material_costs": material_costs
            }
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500


# Export blueprint
__all__ = ['production_bp']
