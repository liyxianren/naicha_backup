"""
Employee API Blueprint
Handles employee management endpoints
"""
from flask import Blueprint, request, jsonify
from app.services.employee_service import EmployeeService
from app.models.player import Player, Employee

employee_bp = Blueprint('employee', __name__)


@employee_bp.route('/hire', methods=['POST'])
def hire_employee():
    """
    Hire a new employee

    Request body:
    {
        "player_id": 1,
        "name": "John",
        "salary": 1000,
        "productivity": 5,
        "round_number": 1
    }

    Response:
    {
        "success": true,
        "data": {
            "id": 1,
            "shop_id": 1,
            "name": "John",
            "salary": 1000.0,
            "productivity": 5,
            "hired_round": 1,
            "is_active": true
        }
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "Request body is required"}), 400

        player_id = data.get('player_id')
        name = data.get('name')
        salary = data.get('salary')
        productivity = data.get('productivity')
        round_number = data.get('round_number')

        if not player_id:
            return jsonify({"success": False, "error": "player_id is required"}), 400
        if not name:
            return jsonify({"success": False, "error": "name is required"}), 400
        if salary is None:
            return jsonify({"success": False, "error": "salary is required"}), 400
        if productivity is None:
            return jsonify({"success": False, "error": "productivity is required"}), 400
        if not round_number:
            return jsonify({"success": False, "error": "round_number is required"}), 400

        # Hire employee
        employee = EmployeeService.hire_employee(
            player_id, name, salary, productivity, round_number
        )

        return jsonify({
            "success": True,
            "data": {
                **employee.to_dict(),
                "remaining_cash": float(Player.query.get(player_id).cash)
            }
        }), 201

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


@employee_bp.route('/<int:employee_id>/fire', methods=['POST'])
def fire_employee(employee_id: int):
    """
    Fire an employee

    Response:
    {
        "success": true,
        "message": "Employee John has been fired",
        "employee_id": 1
    }
    """
    try:
        result = EmployeeService.fire_employee(employee_id)

        return jsonify(result), 200

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


@employee_bp.route('/<int:employee_id>', methods=['GET'])
def get_employee_info(employee_id: int):
    """
    Get employee information

    Response:
    {
        "success": true,
        "data": {
            "id": 1,
            "shop_id": 1,
            "name": "John",
            "salary": 1000.0,
            "productivity": 5,
            "hired_round": 1,
            "is_active": true
        }
    }
    """
    try:
        result = EmployeeService.get_employee_info(employee_id)

        return jsonify({
            "success": True,
            "data": result
        }), 200

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


@employee_bp.route('/player/<int:player_id>', methods=['GET'])
def get_shop_employees(player_id: int):
    """
    Get all employees for a player's shop

    Query parameters:
        include_inactive: Include inactive (fired) employees (default: false)

    Response:
    {
        "success": true,
        "data": [
            {
                "id": 1,
                "shop_id": 1,
                "name": "John",
                "salary": 1000.0,
                "productivity": 5,
                "hired_round": 1,
                "is_active": true
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

        # Get query parameters
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'

        # Get employees
        result = EmployeeService.get_shop_employees(player_id, include_inactive)

        return jsonify({
            "success": True,
            "data": result
        }), 200

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


@employee_bp.route('/player/<int:player_id>/productivity', methods=['GET'])
def get_total_productivity(player_id: int):
    """
    Get total productivity for a player

    Response:
    {
        "success": true,
        "data": {
            "player_id": 1,
            "total_productivity": 15
        }
    }
    """
    try:
        # Verify player exists
        player = Player.query.get(player_id)
        if not player:
            return jsonify({"success": False, "error": f"Player {player_id} not found"}), 404

        # Calculate total productivity
        total = EmployeeService.calculate_total_productivity(player_id)

        return jsonify({
            "success": True,
            "data": {
                "player_id": player_id,
                "total_productivity": total
            }
        }), 200

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


@employee_bp.route('/<int:employee_id>/salary', methods=['PATCH'])
def update_employee_salary(employee_id: int):
    """
    Update employee salary

    Request body:
    {
        "new_salary": 1200
    }

    Response:
    {
        "success": true,
        "data": {
            "employee_id": 1,
            "employee_name": "John",
            "previous_salary": 1000.0,
            "new_salary": 1200.0
        }
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "Request body is required"}), 400

        new_salary = data.get('new_salary')

        if new_salary is None:
            return jsonify({"success": False, "error": "new_salary is required"}), 400

        # Update salary
        result = EmployeeService.update_employee_salary(employee_id, new_salary)

        return jsonify({
            "success": True,
            "data": result
        }), 200

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


# Export blueprint
__all__ = ['employee_bp']
