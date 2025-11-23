"""
核心计算引擎
包含：口碑分计算、客流分配算法、批量折扣计算
"""
from typing import List, Dict, Tuple
from itertools import groupby
import random
from app.core.database import db
from app.models.game import CustomerFlow
from app.models.player import Player
from app.models.product import PlayerProduct, RoundProduction
from app.utils.game_constants import GameConstants


class ReputationCalculator:
    """口碑分计算器"""

    @staticmethod
    def calculate(player_product: PlayerProduct, ad_score: float = None) -> float:
        """
        计算产品的口碑分
        
        公式: 口碑分 = 广告分 + (动态圈粉率 × 累计销售杯数)
        动态圈粉率: 基础圈粉率 - (解锁人数-1)*5%
        - 若历史销量为0且广告分为0，使用圈粉率作为最小基线，避免首轮口碑为0导致低消费客流无法分配
        """
        base_rate = float(player_product.recipe.base_fan_rate)
        
        # Calculate number of players who unlocked this recipe in the same game
        unlocked_count = PlayerProduct.query.join(Player).filter(
            PlayerProduct.recipe_id == player_product.recipe_id,
            PlayerProduct.is_unlocked == True,
            Player.game_id == player_product.player.game_id
        ).count()
        
        # Dynamic Fan Rate: Base - (Count - 1) * 5%
        decay = (unlocked_count - 1) * 5.0
        actual_rate = max(base_rate - decay, 5.0)
        actual_rate_decimal = actual_rate / 100.0

        ad_score_value = ad_score if ad_score is not None else (player_product.current_ad_score or 0)
        total_sold = player_product.total_sold or 0
        
        reputation = ad_score_value + (actual_rate_decimal * total_sold)
        # 基线：避免首轮口碑为0
        minimum_reputation = max(actual_rate_decimal, 0.01)
        if reputation <= 0:
            reputation = minimum_reputation
        return float(reputation)

    @staticmethod
    def calculate_for_production(production: RoundProduction, player_product: PlayerProduct) -> float:
        """
        为某个生产计划计算口碑分

        Args:
            production: 回合生产记录
            player_product: 玩家产品对象

        Returns:
            口碑分
        """
        return ReputationCalculator.calculate(player_product)


class CustomerFlowAllocator:
    """
    客流分配算法 - 游戏的核心算法

    负责根据口碑分、定价、生产力分配客流给各个产品
    """

    @staticmethod
    def allocate(game_id: int, round_number: int) -> Dict:
        """
        执行客流分配 - 主函数
        """
        # 1. 获取客流量
        customer_flow = CustomerFlow.query.filter_by(
            game_id=game_id,
            round_number=round_number
        ).first()

        if not customer_flow:
            raise ValueError(f"未找到游戏 {game_id} 第 {round_number} 回合的客流量数据")

        high_tier_total = customer_flow.high_tier_customers
        low_tier_total = customer_flow.low_tier_customers

        # 2. 获取所有产品数据
        products = CustomerFlowAllocator._get_all_products(game_id, round_number)

        if not products:
            return {
                "high_tier_served": 0,
                "low_tier_served": 0,
                "total_revenue": 0.0,
                "sales_details": []
            }

        # Reset counters
        for p in products:
            p['sold_high'] = 0
            p['sold_low'] = 0
            p['sold_temp'] = 0 

        # 3. 分配高购买力客户
        # 优先级: 口碑(高->低) > 价格(低->高)
        def high_tier_key(p): return (-p['reputation'], p['price'])
        
        remaining_high = CustomerFlowAllocator._distribute_logic(
            products, high_tier_total, high_tier_key
        )
        # 提交临时销量
        for p in products:
            p['sold_high'] = p['sold_temp']
            p['sold_temp'] = 0

        # 4. 分配低购买力客户
        # 优先级: 价格(低->高) > 口碑(高->低)
        # 且 口碑 > 0
        def low_tier_key(p): return (p['price'], -p['reputation'])
        
        remaining_low = CustomerFlowAllocator._distribute_logic(
            products, low_tier_total, low_tier_key, is_low_tier=True
        )
        # 提交临时销量
        for p in products:
            p['sold_low'] = p['sold_temp']
            p['sold_temp'] = 0

        # 5. 保存销售结果
        total_revenue = CustomerFlowAllocator._save_sales(products)

        return {
            "high_tier_served": high_tier_total - remaining_high,
            "low_tier_served": low_tier_total - remaining_low,
            "total_revenue": total_revenue,
            "sales_details": products
        }

    @staticmethod
    def _distribute_logic(products: List[Dict], customer_count: int, sort_key, is_low_tier: bool = False) -> int:
        """
        通用分配逻辑：支持分组平分
        """
        remaining_customers = customer_count
        
        # 1. 排序
        sorted_products = sorted(products, key=sort_key)
        
        # 2. 分组处理 (Handling Ties)
        for key, group_iter in groupby(sorted_products, key=sort_key):
            if remaining_customers <= 0:
                break
                
            group = list(group_iter)
            
            # 低消费客户只买口碑>0
            if is_low_tier:
                group = [p for p in group if p['reputation'] > 0]
                if not group:
                    continue

            # 检查该组总库存
            total_available = sum(p['available'] for p in group)
            if total_available == 0:
                continue

            # 分配逻辑
            if remaining_customers >= total_available:
                # 需求 > 供给：全部卖光
                for p in group:
                    sold = p['available']
                    p['sold_temp'] += sold
                    p['available'] = 0
                    remaining_customers -= sold
            else:
                # 需求 < 供给：需要在组内平分
                # 迭代平分算法
                active_products = list(group)
                while remaining_customers > 0 and active_products:
                    count = len(active_products)
                    share = remaining_customers // count
                    remainder = remaining_customers % count
                    
                    if share == 0:
                        # 随机分配余数
                        import random
                        random.shuffle(active_products)
                        for i in range(remainder):
                            if active_products[i]['available'] > 0:
                                active_products[i]['sold_temp'] += 1
                                active_products[i]['available'] -= 1
                                remaining_customers -= 1
                        break
                    
                    # 分配份额
                    next_active = []
                    for p in active_products:
                        can_sell = min(p['available'], share)
                        p['sold_temp'] += can_sell
                        p['available'] -= can_sell
                        remaining_customers -= can_sell
                        
                        if p['available'] > 0:
                            next_active.append(p)
                            
                    active_products = next_active

        return remaining_customers

    @staticmethod
    def _get_all_products(game_id: int, round_number: int) -> List[Dict]:
        """
        获取所有玩家的所有产品数据

        Returns:
            [
                {
                    "production_id": int,
                    "player_id": int,
                    "product_name": str,
                    "reputation": float,
                    "price": float,
                    "available": int,  # 可售数量
                    "sold_high": int,  # 卖给高购买力客户数量
                    "sold_low": int    # 卖给低购买力客户数量
                },
                ...
            ]
        """
        products = []
        # 当回合广告分（线下骰子）映射：player_id -> ad_score
        from app.models.finance import MarketAction
        ad_scores = {
            action.player_id: action.result_value or 0
            for action in MarketAction.query.filter_by(
                round_number=round_number,
                action_type='ad'
            ).all()
        }

        # 获取游戏中的所有玩家
        players = Player.query.filter_by(game_id=game_id, is_active=True).all()

        for player in players:
            # 获取玩家本回合的生产计划
            productions = RoundProduction.query.filter_by(
                player_id=player.id,
                round_number=round_number
            ).all()

            for prod in productions:
                # 跳过没有生产的产品
                if prod.produced_quantity <= 0:
                    continue

                # 获取玩家产品信息
                player_product = PlayerProduct.query.get(prod.product_id)
                if not player_product or not player_product.is_unlocked:
                    continue

                # 计算口碑分
                ad_score = ad_scores.get(player.id, player_product.current_ad_score or 0)
                reputation = ReputationCalculator.calculate(player_product, ad_score=ad_score)

                products.append({
                    "production_id": prod.id,
                    "player_id": player.id,
                    "player_name": player.nickname,
                    "product_name": player_product.recipe.name,
                    "reputation": reputation,
                    "ad_score": ad_score,
                    "price": float(prod.price),
                    "available": prod.produced_quantity,
                    "sold_high": 0,
                    "sold_low": 0
                })

        return products


    @staticmethod
    def _save_sales(products: List[Dict]) -> float:
        """
        保存销售结果到数据库

        Args:
            products: 产品销售数据列表

        Returns:
            总营业额
        """
        total_revenue = 0.0

        for product in products:
            prod = RoundProduction.query.get(product['production_id'])
            if not prod:
                continue

            total_sold = product['sold_high'] + product['sold_low']
            revenue = total_sold * product['price']

            # 更新生产记录
            prod.sold_quantity = total_sold
            prod.sold_to_high_tier = product['sold_high']
            prod.sold_to_low_tier = product['sold_low']
            prod.revenue = revenue

            total_revenue += revenue

            # 更新玩家产品的累计销售数
            player_product = PlayerProduct.query.get(prod.product_id)
            if player_product:
                player_product.total_sold += total_sold

        # 提交数据库更改
        db.session.commit()

        return total_revenue


class DiscountCalculator:
    """批量折扣计算器"""

    @staticmethod
    def calculate_discount_price(quantity: int, base_unit_price: float) -> float:
        """
        计算批量折扣后的单价

        规则：
        - 每购买50份，价格-10%
        - 最多5次折扣（即最低至原价的50%）
        - 0-49份: 100%原价
        - 50-99份: 90%原价
        - 100-149份: 80%原价
        - 150-199份: 70%原价
        - 200-249份: 60%原价
        - 250+份: 50%原价

        Args:
            quantity: 购买数量
            base_unit_price: 基础单价

        Returns:
            折后单价
        """
        if quantity <= 0:
            return base_unit_price

        # 计算折扣档次
        discount_tier = min(quantity // GameConstants.DISCOUNT_TIER_SIZE,
                           GameConstants.MAX_DISCOUNT_TIERS)

        # 计算折扣率
        discount_rate = 1.0 - (discount_tier * GameConstants.DISCOUNT_PER_TIER)

        return base_unit_price * discount_rate

    @staticmethod
    def calculate_total_cost(quantity: int, base_unit_price: float) -> float:
        """
        计算总成本（数量 × 折后单价）

        Args:
            quantity: 购买数量
            base_unit_price: 基础单价

        Returns:
            总成本
        """
        discounted_price = DiscountCalculator.calculate_discount_price(
            quantity, base_unit_price
        )
        return quantity * discounted_price

    @staticmethod
    def calculate_material_costs(material_needs: Dict[str, int]) -> Dict[str, float]:
        """
        计算所有原材料的总成本（含批量折扣）

        Args:
            material_needs: {"tea": 10, "milk": 20, "fruit": 15, "ingredient": 5}

        Returns:
            {
                "tea": {"quantity": 10, "unit_price": 5.4, "total": 54.0},
                "milk": {"quantity": 20, "unit_price": 3.6, "total": 72.0},
                ...
                "total_cost": 总成本
            }
        """
        costs = {}
        total_cost = 0.0

        for material, quantity in material_needs.items():
            if quantity <= 0:
                continue

            base_price = GameConstants.MATERIAL_BASE_PRICES.get(material, 0)
            if base_price <= 0:
                continue

            # 计算折后单价
            unit_price = DiscountCalculator.calculate_discount_price(
                quantity, base_price
            )

            # 计算折扣率
            discount_tier = min(quantity // GameConstants.DISCOUNT_TIER_SIZE,
                               GameConstants.MAX_DISCOUNT_TIERS)
            discount_rate = 1.0 - (discount_tier * GameConstants.DISCOUNT_PER_TIER)

            # 计算总价
            material_total = quantity * unit_price

            costs[material] = {
                "quantity": quantity,
                "unit_price": round(unit_price, 2),
                "total": round(material_total, 2),
                "discount_rate": round(discount_rate, 2)
            }

            total_cost += material_total

        costs["total_cost"] = round(total_cost, 2)

        return costs


# 导出类
__all__ = ['ReputationCalculator', 'CustomerFlowAllocator', 'DiscountCalculator']
