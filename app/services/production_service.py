"""
生产决策服务
处理生产计划提交、原材料计算、生产力验证等
"""
from typing import List, Dict
from decimal import Decimal
from app.core.database import db
from app.models.player import Player, Employee
from app.models.product import PlayerProduct, ProductRecipe, RoundProduction
from app.services.calculation_engine import DiscountCalculator
from app.utils.game_constants import GameConstants


class ProductionService:
    """生产决策服务"""

    @staticmethod
    def submit_production_plan(player_id: int, round_number: int, productions: List[Dict]) -> Dict:
        """
        提交生产计划

        Args:
            player_id: 玩家ID
            round_number: 回合数
            productions: [
                {"product_id": 1, "productivity": 5, "price": 15},
                {"product_id": 2, "productivity": 10, "price": 25}
            ]

        Returns:
            {
                "success": True,
                "material_needs": {"tea": 10, "milk": 20, ...},
                "material_costs": {"tea": {...}, "total_cost": 123.45},
                "remaining_cash": 8876.55
            }

        Raises:
            ValueError: 各种验证错误
        """
        # 标准化输入，确保数值类型正确
        normalized_productions = []
        for prod in productions:
            if 'product_id' not in prod:
                raise ValueError("缺少 product_id")
            try:
                price_val = float(prod.get('price', 0))
            except Exception:
                raise ValueError("price 必须是数字")
            try:
                productivity_val = int(prod.get('productivity', 0) or 0)
            except Exception:
                raise ValueError("productivity 必须是整数")
            normalized_productions.append({
                "product_id": prod["product_id"],
                "price": price_val,
                "productivity": productivity_val
            })

        player = Player.query.get(player_id)
        if not player:
            raise ValueError(f"玩家 {player_id} 不存在")

        # 1. 验证生产力分配
        total_productivity = ProductionService._get_total_productivity(player_id)
        ProductionService._validate_productivity_allocation(
            normalized_productions, total_productivity
        )

        # 2. 验证定价
        ProductionService._validate_pricing(normalized_productions)

        # 2.5. 验证定价锁定（每3回合可调整）
        ProductionService._validate_price_lock(player_id, round_number, normalized_productions)

        # 3. 验证产品是否已解锁
        ProductionService._validate_products_unlocked(player_id, normalized_productions)

        # 4. 计算原材料需求
        material_needs = ProductionService.calculate_material_needs(normalized_productions)

        # 5. 计算原材料成本（含批量折扣）
        material_costs = DiscountCalculator.calculate_material_costs(material_needs)
        purchase_cost = material_costs["total_cost"]

        # 6. 检查余额
        if player.cash < purchase_cost:
            raise ValueError(
                f"现金不足！需要 {purchase_cost} 元，当前余额 {float(player.cash)} 元"
            )

        # 7. 扣除原材料成本（转换为Decimal避免类型错误）
        player.cash -= Decimal(str(purchase_cost))

        # 8. 删除该玩家本回合的旧生产计划（如果有）
        RoundProduction.query.filter_by(
            player_id=player_id,
            round_number=round_number
        ).delete()

        # 9. 保存新的生产计划并更新产品价格
        for prod_data in normalized_productions:
            if prod_data['productivity'] <= 0:
                continue

            production = RoundProduction(
                player_id=player_id,
                round_number=round_number,
                product_id=prod_data['product_id'],
                allocated_productivity=prod_data['productivity'],
                price=prod_data['price'],
                produced_quantity=prod_data['productivity']  # 生产力 = 生产数量
            )
            db.session.add(production)

            # Update player_product price and last_price_change_round if price changed
            player_product = PlayerProduct.query.get(prod_data['product_id'])
            if player_product and player_product.current_price != prod_data['price']:
                player_product.current_price = prod_data['price']
                player_product.last_price_change_round = round_number

        # 10. 提交所有更改
        db.session.commit()

        return {
            "success": True,
            "material_needs": material_needs,
            "material_costs": material_costs,
            "remaining_cash": float(player.cash)
        }

    @staticmethod
    def get_production_plan(player_id: int, round_number: int) -> List[Dict]:
        """
        获取玩家某回合的生产计划

        Returns:
            [
                {
                    "id": 1,
                    "product_id": 1,
                    "product_name": "奶茶",
                    "allocated_productivity": 5,
                    "price": 15.0,
                    "produced_quantity": 5,
                    "sold_quantity": 3,
                    "revenue": 45.0
                },
                ...
            ]
        """
        productions = RoundProduction.query.filter_by(
            player_id=player_id,
            round_number=round_number
        ).all()

        result = []
        for prod in productions:
            player_product = PlayerProduct.query.get(prod.product_id)

            result.append({
                "id": prod.id,
                "product_id": prod.product_id,
                "product_name": player_product.recipe.name if player_product else "未知",
                "allocated_productivity": prod.allocated_productivity,
                "price": float(prod.price) if prod.price else 0,
                "produced_quantity": prod.produced_quantity,
                "sold_quantity": prod.sold_quantity,
                "sold_to_high_tier": prod.sold_to_high_tier,
                "sold_to_low_tier": prod.sold_to_low_tier,
                "revenue": float(prod.revenue)
            })

        return result

    @staticmethod
    def calculate_material_needs(productions: List[Dict]) -> Dict[str, int]:
        """
        计算原材料总需求

        Args:
            productions: 生产计划列表

        Returns:
            {"tea": 15, "milk": 25, "fruit": 0, "ingredient": 10}
        """
        needs = {"tea": 0, "milk": 0, "fruit": 0, "ingredient": 0}

        for prod_data in productions:
            if prod_data['productivity'] <= 0:
                continue

            # 获取产品配方
            player_product = PlayerProduct.query.get(prod_data['product_id'])
            if not player_product:
                continue

            recipe = player_product.recipe
            quantity = prod_data['productivity']

            # 解析配方 JSON: {"tea": 1, "milk": 2, ...}
            recipe_dict = recipe.recipe_json
            for material, amount_per_unit in recipe_dict.items():
                if material in needs:
                    needs[material] += amount_per_unit * quantity

        return needs

    @staticmethod
    def _get_total_productivity(player_id: int) -> int:
        """
        获取玩家的总生产力（所有在职员工的生产力之和）

        Args:
            player_id: 玩家ID

        Returns:
            总生产力
        """
        player = Player.query.get(player_id)
        if not player or not player.shop:
            return 0

        employees = Employee.query.filter_by(
            shop_id=player.shop.id,
            is_active=True
        ).all()

        return sum(emp.productivity for emp in employees)

    @staticmethod
    def _validate_productivity_allocation(productions: List[Dict], total_productivity: int):
        """
        验证生产力分配是否合法

        Raises:
            ValueError: 如果分配的生产力超过总生产力
        """
        allocated = sum(p['productivity'] for p in productions)

        if allocated > total_productivity:
            raise ValueError(
                f"生产力分配超限！已分配 {allocated}，可用 {total_productivity}"
            )

    @staticmethod
    def _validate_pricing(productions: List[Dict]):
        """
        验证定价是否合法

        规则：定价必须是10-40元之间的5的倍数

        Raises:
            ValueError: 如果定价不合法
        """
        for prod_data in productions:
            price = float(prod_data['price'])

            if price < GameConstants.MIN_PRICE or price > GameConstants.MAX_PRICE:
                raise ValueError(
                    f"定价必须在 {GameConstants.MIN_PRICE}-{GameConstants.MAX_PRICE} 元之间，"
                    f"当前为 {price} 元"
                )

            if price % GameConstants.PRICE_STEP != 0:
                raise ValueError(
                    f"定价必须是 {GameConstants.PRICE_STEP} 的倍数，当前为 {price} 元"
                )

    @staticmethod
    def _validate_products_unlocked(player_id: int, productions: List[Dict]):
        """
        验证所有产品是否已解锁

        Raises:
            ValueError: 如果产品未解锁
        """
        for prod_data in productions:
            if prod_data['productivity'] <= 0:
                continue

            player_product = PlayerProduct.query.get(prod_data['product_id'])

            if not player_product:
                raise ValueError(f"产品 {prod_data['product_id']} 不存在")

            if player_product.player_id != player_id:
                raise ValueError(f"产品 {prod_data['product_id']} 不属于玩家 {player_id}")

            if not player_product.is_unlocked:
                raise ValueError(
                    f"产品 {player_product.recipe.name} 尚未解锁，请先研发"
                )

    @staticmethod
    def _validate_price_lock(player_id: int, round_number: int, productions: List[Dict]):
        """
        验证定价锁定（每3回合可调整一次）

        规则：如果某产品在X回合设置了价格，则在X+1和X+2回合不能修改价格
             只有到X+3回合时才能再次修改

        Args:
            player_id: 玩家ID
            round_number: 当前回合数
            productions: 生产计划列表

        Raises:
            ValueError: 如果尝试在锁定期内修改价格
        """
        for prod_data in productions:
            if prod_data['productivity'] <= 0:
                continue

            player_product = PlayerProduct.query.get(prod_data['product_id'])
            if not player_product:
                continue

            # Check if price is being changed
            new_price = prod_data['price']
            current_price = player_product.current_price
            last_change_round = player_product.last_price_change_round or 0

            if current_price is None:
                continue

            if float(current_price) == float(new_price):
                continue

            rounds_since_change = round_number - last_change_round
            if last_change_round > 0 and rounds_since_change < 3:
                raise ValueError(
                    f"产品 {player_product.recipe.name} 定价已锁定为 {float(current_price)} 元，需等待 {3 - rounds_since_change} 回合后再调整"
                )


# 导出
__all__ = ['ProductionService']
