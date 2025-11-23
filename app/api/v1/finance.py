"""
Finance API Blueprint
Handles finance record queries and financial reports
"""
from flask import Blueprint, request, jsonify
from app.services.finance_service import FinanceService
from app.models.player import Player
from app.models.game import Game

finance_bp = Blueprint('finance', __name__)


@finance_bp.route('/<int:player_id>/<int:round_number>', methods=['GET'])
def get_finance_record(player_id: int, round_number: int):
    """
    Get finance record for a player in a specific round

    Args:
        player_id: Player ID
        round_number: Round number

    Response:
    {
        "success": true,
        "data": {
            "id": 1,
            "player_id": 1,
            "round_number": 1,
            "revenue": {...},
            "expenses": {...},
            "profit": {...}
        }
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

        # Get finance record
        result = FinanceService.get_finance_record(player_id, round_number)

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


@finance_bp.route('/<int:player_id>/all', methods=['GET'])
def get_all_finance_records(player_id: int):
    """
    Get all finance records for a player

    Args:
        player_id: Player ID

    Response:
    {
        "success": true,
        "data": [
            {...},
            {...}
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

        # Get all records
        result = FinanceService.get_all_finance_records(player_id)

        return jsonify({
            "success": True,
            "data": result
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500


@finance_bp.route('/game/<int:game_id>/profit-summary', methods=['GET'])
def get_profit_summary(game_id: int):
    """
    Get profit summary for all players in a game (leaderboard)

    Args:
        game_id: Game ID

    Response:
    {
        "success": true,
        "data": {
            "game_id": 1,
            "current_round": 3,
            "players": [
                {
                    "player_id": 1,
                    "nickname": "Player 1",
                    "total_profit": 5000.0,
                    "cash": 12000.0,
                    "rank": 1
                },
                ...
            ]
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

        # Get profit summary
        result = FinanceService.get_profit_summary(game_id)

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


@finance_bp.route('/<int:player_id>/detailed-report', methods=['GET'])
def get_detailed_report(player_id: int):
    """
    Get detailed financial report for a player

    Args:
        player_id: Player ID

    Response:
    {
        "success": true,
        "data": {
            "player_id": 1,
            "nickname": "Player 1",
            "current_cash": 12000.0,
            "total_profit": 5000.0,
            "rounds": [...]
        }
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

        # Get detailed report
        result = FinanceService.get_detailed_report(player_id)

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


@finance_bp.route('/<int:player_id>/<int:round_number>/generate', methods=['POST'])
def generate_finance_record(player_id: int, round_number: int):
    """
    Generate finance record for a player in a specific round (admin/debug use)

    Args:
        player_id: Player ID
        round_number: Round number

    Response:
    {
        "success": true,
        "data": {...}
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

        # Generate finance record
        record = FinanceService.generate_finance_record(player_id, round_number)

        return jsonify({
            "success": True,
            "data": record.to_dict()
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


# Export blueprint
__all__ = ['finance_bp']
