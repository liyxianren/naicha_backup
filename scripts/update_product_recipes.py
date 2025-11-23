"""
更新产品配方表的数据（难度值从1-3改为3-5）
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.product import ProductRecipe
from app.utils.game_constants import GameConstants

def update_product_recipes():
    """更新数据库中的产品配方数据"""
    print("=" * 60)
    print("🔄 开始更新产品配方数据...")
    print("=" * 60)

    db = SessionLocal()

    try:
        # 从 GameConstants 获取最新的配方数据
        recipes = GameConstants.PRODUCT_RECIPES

        print(f"\n📦 准备更新 {len(recipes)} 个产品配方...\n")

        for recipe_data in recipes:
            name = recipe_data['name']

            # 查找数据库中的产品
            product = db.query(ProductRecipe).filter(ProductRecipe.name == name).first()

            if product:
                # 更新产品数据
                old_difficulty = product.difficulty
                product.difficulty = recipe_data['difficulty']
                product.base_fan_rate = recipe_data['base_fan_rate']
                product.cost_per_unit = recipe_data['cost_per_unit']
                product.recipe_json = recipe_data['recipe_json']

                print(f"✓ 更新 {name}:")
                print(f"  - 难度: {old_difficulty} → {recipe_data['difficulty']}")
                print(f"  - 圈粉率: {recipe_data['base_fan_rate']}%")
                print(f"  - 配方: {recipe_data['recipe_json']}")
            else:
                # 如果产品不存在，创建新产品
                product = ProductRecipe(
                    name=name,
                    difficulty=recipe_data['difficulty'],
                    base_fan_rate=recipe_data['base_fan_rate'],
                    cost_per_unit=recipe_data['cost_per_unit'],
                    recipe_json=recipe_data['recipe_json']
                )
                db.add(product)
                print(f"✓ 创建 {name} (难度{recipe_data['difficulty']})")

        # 提交事务
        db.commit()

        print("\n" + "=" * 60)
        print("✅ 产品配方数据更新成功!")
        print("=" * 60)

        # 显示更新后的数据
        print("\n📋 当前产品配方:")
        products = db.query(ProductRecipe).order_by(ProductRecipe.id).all()
        for p in products:
            print(f"  {p.id}. {p.name:<8} - 难度{p.difficulty} - 圈粉率{p.base_fan_rate}% - 配方{p.recipe_json}")

    except Exception as e:
        db.rollback()
        print(f"\n❌ 更新失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        db.close()

if __name__ == "__main__":
    update_product_recipes()
