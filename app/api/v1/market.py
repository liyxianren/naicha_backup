"""
Market API Blueprint
Handles market action endpoints (advertisement, market research)
"""
from flask import Blueprint, request, jsonify
from app.services.market_service import MarketService
from app.models.player import Player

market_bp = Blueprint('market', __name__)


@market_bp.route('/advertisement', methods=['POST'])
def place_advertisement():
    """
    Place advertisement (player-level, offline dice)
    Request body:
    {
        "player_id": 1,
        "round_number": 1,
        "dice_result": 5
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "Request body is required"}), 400

        player_id = data.get('player_id')
        round_number = data.get('round_number')
        dice_result = data.get('dice_result')

        if not player_id:
            return jsonify({"success": False, "error": "player_id is required"}), 400
        if not round_number:
            return jsonify({"success": False, "error": "round_number is required"}), 400
        if dice_result is None:
            return jsonify({"success": False, "error": "dice_result is required"}), 400

        result = MarketService.place_advertisement(player_id, round_number, dice_result)

        return jsonify({"success": True, "data": result}), 200

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


@market_bp.route('/research', methods=['POST'])
def conduct_market_research():
    """
    Conduct market research to view NEXT round's customer flow
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "Request body is required"}), 400

        player_id = data.get('player_id')
        round_number = data.get('round_number')

        if not player_id:
            return jsonify({"success": False, "error": "player_id is required"}), 400
        if not round_number:
            return jsonify({"success": False, "error": "round_number is required"}), 400

        result = MarketService.conduct_market_research(player_id, round_number)

        return jsonify({"success": True, "data": result}), 200

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


@market_bp.route('/actions/<int:player_id>', methods=['GET'])
def get_market_actions(player_id: int):
    """
    Get market actions for a player
    """
    try:
        player = Player.query.get(player_id)
        if not player:
            return jsonify({"success": False, "error": f"Player {player_id} not found"}), 404

        round_number = request.args.get('round_number', type=int)
        result = MarketService.get_market_actions(player_id, round_number)

        return jsonify({"success": True, "data": result}), 200

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


@market_bp.route('/costs', methods=['GET'])
def get_action_costs():
    """Get costs for all market actions"""
    try:
        result = MarketService.get_action_costs()
        return jsonify({"success": True, "data": result}), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


__all__ = ['market_bp']
