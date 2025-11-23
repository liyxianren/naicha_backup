"""
添加turn_order字段到players表
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import db
from app.main import app
from sqlalchemy import text

if __name__ == '__main__':
    with app.app_context():
        try:
            # 添加turn_order字段
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE players ADD COLUMN turn_order INT DEFAULT 0'))
                conn.commit()
            print("✅ turn_order字段添加成功！")
        except Exception as e:
            print(f"⚠️ 添加字段失败（可能已存在）: {e}")

        # 为现有玩家设置turn_order
        try:
            with db.engine.connect() as conn:
                # 根据player_number设置turn_order
                conn.execute(text('UPDATE players SET turn_order = player_number - 1 WHERE turn_order IS NULL OR turn_order = 0'))
                conn.commit()
            print("✅ 现有玩家turn_order更新成功！")
        except Exception as e:
            print(f"⚠️ 更新失败: {e}")
