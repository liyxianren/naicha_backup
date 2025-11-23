from app.core.database import db
from app.models.game import Game, CustomerFlow
from app.models.player import Player
from app.models.product import ProductRecipe, PlayerProduct, RoundProduction
from app.services.calculation_engine import CustomerFlowAllocator


def test_low_tier_customers_can_buy_with_zero_history(app_ctx):
    """
    首轮无广告、无历史销量时，低消费客户仍应分配到可生产产品（口碑基线>0）。
    场景：两个玩家各生产10杯，同一配方，价格15/20，低消费客户20。
    预期：低消费客户优先买更便宜的，卖完后买第二个；总计卖出20杯。
    """
    # 基础数据
    game = Game(room_code="TEST01", status="in_progress", current_round=1, max_players=4)
    db.session.add(game)
    db.session.flush()

    p1 = Player(game_id=game.id, nickname="P1", player_number=1, turn_order=1, cash=10000)
    p2 = Player(game_id=game.id, nickname="P2", player_number=2, turn_order=2, cash=10000)
    db.session.add_all([p1, p2])
    db.session.flush()

    recipe = ProductRecipe(
        name="测试奶茶",
        difficulty=3,
        base_fan_rate=5.0,
        cost_per_unit=10.0,
        recipe_json={"milk": 1, "tea": 1},
        is_active=True,
    )
    db.session.add(recipe)
    db.session.flush()

    pp1 = PlayerProduct(player_id=p1.id, recipe_id=recipe.id, is_unlocked=True, total_sold=0, current_price=15)
    pp2 = PlayerProduct(player_id=p2.id, recipe_id=recipe.id, is_unlocked=True, total_sold=0, current_price=20)
    db.session.add_all([pp1, pp2])
    db.session.flush()

    prod1 = RoundProduction(
        player_id=p1.id,
        round_number=1,
        product_id=pp1.id,
        allocated_productivity=10,
        price=15,
        produced_quantity=10,
    )
    prod2 = RoundProduction(
        player_id=p2.id,
        round_number=1,
        product_id=pp2.id,
        allocated_productivity=10,
        price=20,
        produced_quantity=10,
    )
    db.session.add_all([prod1, prod2])

    flow = CustomerFlow(game_id=game.id, round_number=1, high_tier_customers=0, low_tier_customers=20)
    db.session.add(flow)
    db.session.commit()

    result = CustomerFlowAllocator.allocate(game.id, 1)

    # 校验分配结果
    assert result["high_tier_served"] == 0
    assert result["low_tier_served"] == 20

    updated_prod1 = RoundProduction.query.get(prod1.id)
    updated_prod2 = RoundProduction.query.get(prod2.id)

    assert updated_prod1.sold_to_low_tier == 10
    assert updated_prod2.sold_to_low_tier == 10
    assert updated_prod1.sold_quantity == 10
    assert updated_prod2.sold_quantity == 10

    # 累计销量也应同步，避免下一回合口碑失真
    updated_pp1 = PlayerProduct.query.get(pp1.id)
    updated_pp2 = PlayerProduct.query.get(pp2.id)
    assert updated_pp1.total_sold == 10
    assert updated_pp2.total_sold == 10


def test_high_then_low_allocation_respects_reputation_and_price(app_ctx, two_players, make_recipe, unlock_product):
    """
    高消费按口碑优先，口碑相同时价格升序；低消费按价格升序，口碑>0。
    场景：
      - P1 广告分6，价格20，产5
      - P2 广告分0（基线>0），价格10，产10
      客流：高10，低10
    预期：
      - 高消费先买 P1 全部5，再买 P2 5
      - 低消费剩余 5 杯全买 P2（因价格低且有库存）
    """
    game, p1, p2 = two_players
    recipe = make_recipe()

    pp1 = unlock_product(p1.id, recipe.id, price=20, ad_score=0)
    pp2 = unlock_product(p2.id, recipe.id, price=10, ad_score=0)

    # 当回合广告分：P1=6
    from app.models.finance import MarketAction
    db.session.add(MarketAction(player_id=p1.id, round_number=1, action_type="ad", cost=800, result_value=6))
    db.session.commit()

    prod1 = RoundProduction(
        player_id=p1.id,
        round_number=1,
        product_id=pp1.id,
        allocated_productivity=5,
        price=20,
        produced_quantity=5,
    )
    prod2 = RoundProduction(
        player_id=p2.id,
        round_number=1,
        product_id=pp2.id,
        allocated_productivity=10,
        price=10,
        produced_quantity=10,
    )
    db.session.add_all([prod1, prod2])

    flow = CustomerFlow(game_id=game.id, round_number=1, high_tier_customers=10, low_tier_customers=10)
    db.session.add(flow)
    db.session.commit()

    result = CustomerFlowAllocator.allocate(game.id, 1)

    assert result["high_tier_served"] == 10
    # 低消费有10人，但只剩余5杯库存，实际服务5人
    assert result["low_tier_served"] == 5

    updated_prod1 = RoundProduction.query.get(prod1.id)
    updated_prod2 = RoundProduction.query.get(prod2.id)

    assert updated_prod1.sold_to_high_tier == 5
    assert updated_prod1.sold_to_low_tier == 0
    assert updated_prod2.sold_to_high_tier == 5
    assert updated_prod2.sold_to_low_tier == 5

    # 库存应被消费完
    assert updated_prod1.sold_quantity == 5
    assert updated_prod2.sold_quantity == 10
