import pytest
from decimal import Decimal

from app.core.database import db
from app.models.player import Player, Employee
from app.services.production_service import ProductionService
from app.services.calculation_engine import DiscountCalculator
from app.utils.game_constants import GameConstants


def test_price_lock_prevents_change_within_three_rounds(app_ctx, two_players, make_recipe, unlock_product):
    """定价锁：距离上次调价未满3回合，修改应报错。"""
    _, p1, _ = two_players
    recipe = make_recipe()
    product = unlock_product(p1.id, recipe.id, price=20, ad_score=0, unlocked_round=1)
    product.last_price_change_round = 1
    db.session.commit()

    with pytest.raises(ValueError):
        ProductionService._validate_price_lock(
            player_id=p1.id,
            round_number=2,
            productions=[{"product_id": product.id, "price": 25, "productivity": 5}],
        )


def test_price_lock_allows_change_after_three_rounds(app_ctx, two_players, make_recipe, unlock_product):
    """定价锁：满3回合后可修改，不抛异常。"""
    _, p1, _ = two_players
    recipe = make_recipe()
    product = unlock_product(p1.id, recipe.id, price=20, ad_score=0, unlocked_round=1)
    product.last_price_change_round = 1
    db.session.commit()

    # round 4 距离 round1 已满3回合
    ProductionService._validate_price_lock(
        player_id=p1.id,
        round_number=4,
        productions=[{"product_id": product.id, "price": 25, "productivity": 5}],
    )


def test_material_discount_applied():
    """批量折扣：每满50份-10%，最低5折。"""
    base = GameConstants.MATERIAL_BASE_PRICES["tea"]
    # 120 份，折扣 = min(120//50=2,5)*10% =20%，单价应为 base*0.8
    unit_price = DiscountCalculator.calculate_discount_price(quantity=120, base_unit_price=base)
    assert unit_price == pytest.approx(base * 0.8)

    # 超过5档，最低5折
    unit_price_300 = DiscountCalculator.calculate_discount_price(quantity=300, base_unit_price=base)
    assert unit_price_300 == pytest.approx(base * 0.5)
