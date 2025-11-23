"""
Employee service
Handles employee hiring, firing, and management
"""
from typing import Dict, List
from app.core.database import db
from app.models.player import Player, Employee


class EmployeeService:
    """Employee management service"""

    @staticmethod
    def hire_employee(player_id: int, name: str, salary: float, productivity: int, round_number: int) -> Employee:
        """
        Hire a new employee

        Args:
            player_id: Player ID
            name: Employee name
            salary: Monthly salary
            productivity: Productivity value (units per round)
            round_number: Round when employee is hired

        Returns:
            Employee object

        Raises:
            ValueError: Various validation errors
        """
        player = Player.query.get(player_id)
        if not player:
            raise ValueError(f"Player {player_id} not found")

        if not player.shop:
            raise ValueError("Player must have a shop before hiring employees")

        # Check if shop has reached max employees
        current_employees = Employee.query.filter_by(
            shop_id=player.shop.id,
            is_active=True
        ).count()

        if current_employees >= player.shop.max_employees:
            raise ValueError(
                f"Shop has reached maximum employees ({player.shop.max_employees}). "
                f"Upgrade decoration to hire more."
            )

        # Validate salary
        if salary <= 0:
            raise ValueError("Salary must be positive")

        # Check cash and deduct upfront
        if player.cash < salary:
            raise ValueError(f"Insufficient cash to hire employee, need {salary}, have {float(player.cash)}")
        player.cash -= salary

        # Validate productivity
        if productivity <= 0:
            raise ValueError("Productivity must be positive")

        # Create employee
        employee = Employee(
            shop_id=player.shop.id,
            name=name,
            salary=salary,
            productivity=productivity,
            hired_round=round_number,
            is_active=True
        )

        db.session.add(employee)
        db.session.commit()

        return employee

    @staticmethod
    def fire_employee(employee_id: int) -> Dict:
        """
        Fire an employee

        Args:
            employee_id: Employee ID

        Returns:
            {"success": True, "message": "Employee fired"}

        Raises:
            ValueError: If employee not found or already inactive
        """
        employee = Employee.query.get(employee_id)
        if not employee:
            raise ValueError(f"Employee {employee_id} not found")

        if not employee.is_active:
            raise ValueError(f"Employee {employee.name} is already inactive")

        # Mark as inactive instead of deleting
        employee.is_active = False
        db.session.commit()

        return {
            "success": True,
            "message": f"Employee {employee.name} has been fired",
            "employee_id": employee_id
        }

    @staticmethod
    def get_employee_info(employee_id: int) -> Dict:
        """
        Get employee information

        Args:
            employee_id: Employee ID

        Returns:
            Employee information dictionary

        Raises:
            ValueError: If employee not found
        """
        employee = Employee.query.get(employee_id)
        if not employee:
            raise ValueError(f"Employee {employee_id} not found")

        return employee.to_dict()

    @staticmethod
    def get_shop_employees(player_id: int, include_inactive: bool = False) -> List[Dict]:
        """
        Get all employees for a player's shop

        Args:
            player_id: Player ID
            include_inactive: Include inactive (fired) employees

        Returns:
            List of employee dictionaries

        Raises:
            ValueError: If player doesn't have a shop
        """
        player = Player.query.get(player_id)
        if not player:
            raise ValueError(f"Player {player_id} not found")

        if not player.shop:
            raise ValueError("Player doesn't have a shop")

        # Query employees
        query = Employee.query.filter_by(shop_id=player.shop.id)

        if not include_inactive:
            query = query.filter_by(is_active=True)

        employees = query.all()

        return [emp.to_dict() for emp in employees]

    @staticmethod
    def calculate_total_productivity(player_id: int) -> int:
        """
        Calculate total productivity from all active employees

        Args:
            player_id: Player ID

        Returns:
            Total productivity

        Raises:
            ValueError: If player doesn't have a shop
        """
        player = Player.query.get(player_id)
        if not player:
            raise ValueError(f"Player {player_id} not found")

        if not player.shop:
            return 0

        employees = Employee.query.filter_by(
            shop_id=player.shop.id,
            is_active=True
        ).all()

        return sum(emp.productivity for emp in employees)

    @staticmethod
    def calculate_total_salary(player_id: int) -> float:
        """
        Calculate total monthly salary for all active employees

        Args:
            player_id: Player ID

        Returns:
            Total salary

        Raises:
            ValueError: If player doesn't have a shop
        """
        player = Player.query.get(player_id)
        if not player:
            raise ValueError(f"Player {player_id} not found")

        if not player.shop:
            return 0.0

        employees = Employee.query.filter_by(
            shop_id=player.shop.id,
            is_active=True
        ).all()

        return sum(float(emp.salary) for emp in employees)

    @staticmethod
    def update_employee_salary(employee_id: int, new_salary: float) -> Dict:
        """
        Update employee salary

        Args:
            employee_id: Employee ID
            new_salary: New salary amount

        Returns:
            {
                "success": True,
                "employee_id": 1,
                "previous_salary": 1000.0,
                "new_salary": 1200.0
            }

        Raises:
            ValueError: Various validation errors
        """
        employee = Employee.query.get(employee_id)
        if not employee:
            raise ValueError(f"Employee {employee_id} not found")

        if not employee.is_active:
            raise ValueError("Cannot update salary for inactive employee")

        if new_salary <= 0:
            raise ValueError("Salary must be positive")

        previous_salary = float(employee.salary)
        employee.salary = new_salary
        db.session.commit()

        return {
            "success": True,
            "employee_id": employee_id,
            "employee_name": employee.name,
            "previous_salary": previous_salary,
            "new_salary": float(new_salary)
        }


# Export
__all__ = ['EmployeeService']
