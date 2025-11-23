"""
Market service
Handles market actions: advertisement (player-level) and market research.
"""
from typing import Dict, List
from app.core.database import db
from app.models.player import Player
from app.models.finance import MarketAction
from app.utils.game_constants import GameConstants


class MarketService:
    """Market action management service"""

    @staticmethod
    def place_advertisement(player_id: int, round_number: int, dice_result: int) -> Dict:
        """
        Place advertisement (player-level, not per-product)
        - Cost: 800
        - Dice 1-6 sets this round's ad_score for the player
        """
        player = Player.query.get(player_id)
        if not player:
            raise ValueError(f"Player {player_id} not found")

        if dice_result < 1 or dice_result > 6:
            raise ValueError(f"Invalid dice result: {dice_result}. Must be between 1 and 6")

        cost = GameConstants.ADVERTISEMENT_COST
        if player.cash < cost:
            raise ValueError(f"Insufficient cash! Need {cost}, have {float(player.cash)}")

        player.cash -= cost
        # 将本回合广告分同步到玩家所有已解锁产品，供口碑计算使用
        from app.models.product import PlayerProduct
        unlocked_products = PlayerProduct.query.filter_by(
            player_id=player_id,
            is_unlocked=True
        ).all()
        for p in unlocked_products:
            p.current_ad_score = dice_result

        market_action = MarketAction(
            player_id=player_id,
            round_number=round_number,
            action_type='ad',
            cost=cost,
            result_value=dice_result  # store ad_score
        )
        db.session.add(market_action)
        db.session.commit()

        return {
            "success": True,
            "dice_result": dice_result,
            "ad_score": dice_result,
            "cost": cost,
            "remaining_cash": float(player.cash)
        }

    @staticmethod
    def conduct_market_research(player_id: int, round_number: int) -> Dict:
        """
        Conduct market research to view NEXT round's customer flow
        - Cost: 500
        - Reveals customer flow for NEXT round (round_number + 1)
        """
        player = Player.query.get(player_id)
        if not player:
            raise ValueError(f"Player {player_id} not found")

        cost = GameConstants.MARKET_RESEARCH_COST
        if player.cash < cost:
            raise ValueError(f"Insufficient cash! Need {cost}, have {float(player.cash)}")

        player.cash -= cost

        from app.models.game import CustomerFlow
        from app.services.round_service import RoundService

        next_round = round_number + 1

        customer_flow = CustomerFlow.query.filter_by(
            game_id=player.game_id,
            round_number=next_round
        ).first()

        if not customer_flow:
            customer_flow = RoundService.generate_customer_flow(player.game_id, next_round)

        market_action = MarketAction(
            player_id=player_id,
            round_number=round_number,
            action_type='research',
            cost=cost,
            result_value=None
        )
        db.session.add(market_action)
        db.session.commit()

        return {
            "success": True,
            "cost": cost,
            "next_round": next_round,
            "customer_flow": {
                "high_tier_customers": customer_flow.high_tier_customers,
                "low_tier_customers": customer_flow.low_tier_customers
            },
            "remaining_cash": float(player.cash)
        }

    @staticmethod
    def get_market_actions(player_id: int, round_number: int = None) -> List[Dict]:
        player = Player.query.get(player_id)
        if not player:
            raise ValueError(f"Player {player_id} not found")

        query = MarketAction.query.filter_by(player_id=player_id)
        if round_number is not None:
            query = query.filter_by(round_number=round_number)

        actions = query.order_by(MarketAction.round_number.desc()).all()
        return [action.to_dict() for action in actions]

    @staticmethod
    def get_action_costs() -> Dict:
        return {
            "advertisement": GameConstants.ADVERTISEMENT_COST,
            "market_research": GameConstants.MARKET_RESEARCH_COST,
            "product_research": GameConstants.PRODUCT_RESEARCH_COST
        }


__all__ = ['MarketService']
