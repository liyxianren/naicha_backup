import pytest
from decimal import Decimal

from app.core.database import db
from app.services.market_service import MarketService
from app.services.product_service import ProductService
from app.models.finance import MarketAction, ResearchLog
from app.models.player import Player
from app.models.product import ProductRecipe, PlayerProduct
from app.utils.game_constants import GameConstants


def test_advertisement_cost_and_ad_score(app_ctx, two_players, make_recipe, unlock_product):
    """广告应扣费并把广告分同步到已解锁产品，写入 market_actions。"""
    game, p1, _ = two_players
    recipe = make_recipe()
    unlock_product(p1.id, recipe.id, price=20, ad_score=0)

    initial_cash = Player.query.get(p1.id).cash
    resp = MarketService.place_advertisement(p1.id, round_number=1, dice_result=5)

    assert resp["success"] is True
    assert resp["ad_score"] == 5
    assert float(Player.query.get(p1.id).cash) == float(Decimal(initial_cash) - GameConstants.ADVERTISEMENT_COST)

    # 产品广告分同步
    product = PlayerProduct.query.filter_by(player_id=p1.id, recipe_id=recipe.id).first()
    assert product.current_ad_score == 5

    # 记录写入
    action = MarketAction.query.filter_by(player_id=p1.id, round_number=1, action_type="ad").first()
    assert action is not None
    assert action.result_value == 5


def test_research_success_unlocks_and_costs(app_ctx, two_players, make_recipe):
    """研发成功扣费并解锁产品，记录日志与解锁回合。"""
    _, p1, _ = two_players
    recipe = make_recipe(difficulty=3)
    initial_cash = Player.query.get(p1.id).cash

    resp = ProductService.research_product(
        player_id=p1.id,
        recipe_id=recipe.id,
        round_number=2,
        dice_result=6,  # 保证成功
    )

    assert resp["success"] is True
    assert resp["research_success"] is True
    assert resp["product_unlocked"] is True
    assert resp["remaining_cash"] == float(Decimal(initial_cash) - GameConstants.PRODUCT_RESEARCH_COST)

    player_product = PlayerProduct.query.filter_by(player_id=p1.id, recipe_id=recipe.id).first()
    assert player_product.is_unlocked is True
    assert player_product.unlocked_round == 2

    log = ResearchLog.query.filter_by(player_id=p1.id, recipe_id=recipe.id, round_number=2).first()
    assert log is not None
    assert log.success is True


def test_research_fail_still_costs_no_unlock(app_ctx, two_players, make_recipe):
    """研发失败扣费但不解锁产品，仍记录日志。"""
    _, p1, _ = two_players
    recipe = make_recipe(difficulty=6)  # 超难，1d6必失败
    initial_cash = Player.query.get(p1.id).cash

    resp = ProductService.research_product(
        player_id=p1.id,
        recipe_id=recipe.id,
        round_number=1,
        dice_result=1,  # 必失败
    )

    assert resp["success"] is True
    assert resp["research_success"] is False
    assert resp["product_unlocked"] is False
    assert resp["remaining_cash"] == float(Decimal(initial_cash) - GameConstants.PRODUCT_RESEARCH_COST)

    player_product = PlayerProduct.query.filter_by(player_id=p1.id, recipe_id=recipe.id).first()
    assert player_product is None or player_product.is_unlocked is False

    log = ResearchLog.query.filter_by(player_id=p1.id, recipe_id=recipe.id, round_number=1).first()
    assert log is not None
    assert log.success is False
