"""
删除所有游戏房间和玩家数据
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import db
from app.main import app
from app.models.game import Game
from app.models.player import Player

if __name__ == '__main__':
    with app.app_context():
        try:
            # 删除所有玩家
            player_count = Player.query.delete()
            # 删除所有游戏
            game_count = Game.query.delete()

            db.session.commit()

            print(f"Successfully deleted {player_count} players and {game_count} games!")
        except Exception as e:
            db.session.rollback()
            print(f"Error: {e}")
