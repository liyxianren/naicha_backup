"""
使用 Flask app context 更新产品配方数据
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import create_app
from app.core.database import db
from app.models.product import ProductRecipe

def main():
    print("=" * 60)
    print("Starting to update product recipes...")
    print("=" * 60)

    # 创建 Flask 应用
    app = create_app()

    with app.app_context():
        try:
            # 更新难度值
            updates = [
                ('奶茶', 3),
                ('椰奶', 3),
                ('柠檬茶', 3),
                ('果汁', 3),
                ('珍珠奶茶', 4),
                ('水果奶昔', 4),
                ('水果茶', 5),
            ]

            for name, difficulty in updates:
                product = ProductRecipe.query.filter_by(name=name).first()
                if product:
                    old_difficulty = product.difficulty
                    product.difficulty = difficulty
                    print(f"Updated {name}: difficulty {old_difficulty} -> {difficulty}")
                else:
                    print(f"Warning: Product '{name}' not found")

            # 提交事务
            db.session.commit()

            print("\n" + "=" * 60)
            print("Product recipes updated successfully!")
            print("=" * 60)

            # 显示更新后的数据
            print("\nCurrent product recipes:")
            products = ProductRecipe.query.order_by(ProductRecipe.id).all()
            for p in products:
                print(f"  {p.id}. {p.name:<10} - Difficulty {p.difficulty} - Fan rate {p.base_fan_rate}% - Recipe {p.recipe_json}")

        except Exception as e:
            db.session.rollback()
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()
            return 1

    return 0

if __name__ == "__main__":
    exit(main())
