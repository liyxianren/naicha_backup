"""
后台清理不活跃玩家的定时任务。
"""
import threading
import time
from datetime import datetime, timedelta
from app.core.database import db
from app.models.player import Player
from app.models.game import Game


def _cleanup_once(inactive_seconds: int = 300):
    """执行一次清理任务，移除超过 inactive_seconds 未活跃的玩家。"""
    threshold = datetime.utcnow() - timedelta(seconds=inactive_seconds)
    inactive_players = Player.query.filter(
        (Player.last_active_at.is_(None)) | (Player.last_active_at < threshold)
    ).all()

    if not inactive_players:
        return

    affected_game_ids = set()
    for player in inactive_players:
        affected_game_ids.add(player.game_id)
        db.session.delete(player)

    db.session.commit()

    # 删除已空房间
    for game_id in affected_game_ids:
        if Player.query.filter_by(game_id=game_id).count() == 0:
            game = Game.query.get(game_id)
            if game:
                db.session.delete(game)
    db.session.commit()


def start_inactive_player_cleanup(app, interval_seconds: int = 60, inactive_seconds: int = 300):
    """
    启动后台线程定时清理不活跃玩家。
    :param app: Flask app
    :param interval_seconds: 执行周期
    :param inactive_seconds: 判定超时的秒数，默认5分钟
    """

    def worker():
        while True:
            with app.app_context():
                _cleanup_once(inactive_seconds=inactive_seconds)
                # 释放连接，避免后台线程长期占用导致连接失效
                db.session.remove()
            time.sleep(interval_seconds)

    thread = threading.Thread(target=worker, daemon=True, name="inactive-player-cleaner")
    thread.start()
