"""
添加name字段到games表
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
            # 添加name字段
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE games ADD COLUMN name VARCHAR(100)'))
                conn.commit()
            print("name field added successfully!")
        except Exception as e:
            print(f"Error (may already exist): {e}")

        # 为现有游戏设置name为room_code
        try:
            with db.engine.connect() as conn:
                conn.execute(text('UPDATE games SET name = room_code WHERE name IS NULL'))
                conn.commit()
            print("Existing games updated!")
        except Exception as e:
            print(f"Update error: {e}")
