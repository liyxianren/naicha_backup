"""
Round API Blueprint
Handles round progression and round queries
"""
from flask import Blueprint, request, jsonify
from app.services.round_service import RoundService
from app.services.finance_service import FinanceService
from app.models.game import Game
from app.models.player import Player

round_bp = Blueprint('round', __name__)


@round_bp.route('/<int:game_id>/advance', methods=['POST'])
def advance_round(game_id: int):
    """
    Advance to next round

    Args:
        game_id: Game ID

    Response:
    {
        "success": true,
        "data": {
            "previous_round": 1,
            "current_round": 2,
            "customer_flow": {...},
            "allocation_result": {...},
            "game_finished": false
        }
    }
    """
    try:
        # Verify game exists
        game = Game.query.get(game_id)
        if not game:
            return jsonify({
                "success": False,
                "error": f"Game {game_id} not found"
            }), 404

        # Advance round
        result = RoundService.advance_round(game_id)

        # Generate finance records for all players for the previous round
        previous_round = result["previous_round"]
        players = Player.query.filter_by(game_id=game_id, is_active=True).all()

        for player in players:
            try:
                FinanceService.generate_finance_record(player.id, previous_round)
            except Exception as e:
                # Log error but continue
                print(f"Error generating finance record for player {player.id}: {str(e)}")

        return jsonify({
            "success": True,
            "data": result
        }), 200

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

    except Exception as e:
        import traceback
        print(f"Error advancing round {game_id}: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500


@round_bp.route('/<int:game_id>/<int:round_number>/summary', methods=['GET'])
def get_round_summary(game_id: int, round_number: int):
    """
    Get summary of a specific round

    Args:
        game_id: Game ID
        round_number: Round number

    Response:
    {
        "success": true,
        "data": {
            "round_number": 1,
            "customer_flow": {...},
            "players": [...]
        }
    }
    """
    try:
        # Verify game exists
        game = Game.query.get(game_id)
        if not game:
            return jsonify({
                "success": False,
                "error": f"Game {game_id} not found"
            }), 404

        # Get round summary
        result = RoundService.get_round_summary(game_id, round_number)

        return jsonify({
            "success": True,
            "data": result
        }), 200

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500


@round_bp.route('/<int:game_id>/<int:round_number>/generate-flow', methods=['POST'])
def generate_customer_flow(game_id: int, round_number: int):
    """
    Generate customer flow for a specific round (admin/debug use)

    Args:
        game_id: Game ID
        round_number: Round number

    Response:
    {
        "success": true,
        "data": {
            "id": 1,
            "game_id": 1,
            "round_number": 1,
            "high_tier_customers": 25,
            "low_tier_customers": 40
        }
    }
    """
    try:
        # Verify game exists
        game = Game.query.get(game_id)
        if not game:
            return jsonify({
                "success": False,
                "error": f"Game {game_id} not found"
            }), 404

        # Generate customer flow
        customer_flow = RoundService.generate_customer_flow(game_id, round_number)

        return jsonify({
            "success": True,
            "data": customer_flow.to_dict()
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500


# Export blueprint
__all__ = ['round_bp']
