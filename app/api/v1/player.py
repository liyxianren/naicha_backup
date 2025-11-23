"""
玩家相关API (Flask Blueprint)
"""
from flask import Blueprint, request, jsonify
from app.core.database import db
from app.models.game import Game
from app.models.player import Player
from app.models.product import ProductRecipe, PlayerProduct
from datetime import datetime

# 蓝图
player_bp = Blueprint('players', __name__)


def _extract_session_token(data: dict):
    """统一读取 session_token"""
    token = data.get('session_token')
    if not token:
        token = request.headers.get('X-Session-Token')
    if not token:
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '')
    return token


@player_bp.route('/join', methods=['POST'])
def join_game():
    """加入游戏"""
    data = request.get_json() or {}
    game_id = data.get('game_id')
    player_name = data.get('player_name')
    session_token = _extract_session_token(data)

    if not session_token:
        return jsonify({"success": False, "error": "请先登录"}), 401

    if not player_name:
        return jsonify({"success": False, "error": "请输入玩家昵称"}), 400

    if not game_id:
        return jsonify({"success": False, "error": "缺少游戏ID"}), 400

    game = Game.query.get(game_id)

    if not game:
        return jsonify({"success": False, "error": "游戏房间不存在"}), 404

    if game.status != 'waiting':
        return jsonify({"success": False, "error": "游戏已开始，无法加入"}), 400

    # 如果 session 已绑定其他游戏/玩家，视为切换房间：删除旧玩家及空房间
    existing_player = Player.query.filter_by(session_token=session_token).first()
    if existing_player:
        old_game_id = existing_player.game_id
        db.session.delete(existing_player)
        db.session.commit()

        if old_game_id and old_game_id != game.id:
            remaining = Player.query.filter_by(game_id=old_game_id).count()
            if remaining == 0:
                old_game = Game.query.get(old_game_id)
                if old_game:
                    db.session.delete(old_game)
                    db.session.commit()

    # 检查人数
    current_players = Player.query.filter_by(game_id=game.id).count()
    if current_players >= game.max_players:
        return jsonify({"success": False, "error": "房间已满"}), 400

    # 分配唯一的回合顺序
    existing_orders = [p.turn_order for p in Player.query.filter_by(game_id=game.id).all()]
    turn_order = 0
    while turn_order in existing_orders:
        turn_order += 1

    # 创建玩家
    player = Player(
        game_id=game.id,
        nickname=player_name,
        player_number=turn_order + 1,  # player_number从1开始
        turn_order=turn_order,
        cash=10000.00,
        total_profit=0.00,
        is_ready=False,
        session_token=session_token,
        last_active_at=datetime.utcnow()
    )

    db.session.add(player)
    db.session.flush()  # 获取player.id

    # 初始化配方（全部锁定）
    recipes = ProductRecipe.query.all()
    player_products = []
    for recipe in recipes:
        player_products.append(PlayerProduct(
            player_id=player.id,
            recipe_id=recipe.id,
            is_unlocked=False
        ))
    
    db.session.bulk_save_objects(player_products)
    db.session.commit()

    return jsonify({
        "success": True,
        "data": player.to_dict()
    }), 201


@player_bp.route('/<int:player_id>/leave', methods=['POST'])
def leave_game(player_id):
    """离开游戏房间"""
    player = Player.query.get(player_id)

    if not player:
        return jsonify({"success": False, "error": "玩家不存在"}), 404

    game_id = player.game_id

    db.session.delete(player)
    db.session.commit()

    # 如果房间空了，删除房间
    remaining_players = Player.query.filter_by(game_id=game_id).count()
    if remaining_players == 0:
        game = Game.query.get(game_id)
        if game:
            db.session.delete(game)
            db.session.commit()
            return jsonify({
                "success": True,
                "message": "你离开了房间，房间已被清理"
            }), 200

    return jsonify({
        "success": True,
        "message": "已离开房间"
    }), 200


@player_bp.route('/<int:player_id>/ready', methods=['POST'])
def player_ready(player_id):
    """切换准备/取消准备"""
    data = request.get_json() or {}
    is_ready = data.get('is_ready', True)

    player = Player.query.get(player_id)

    if not player:
        return jsonify({"success": False, "error": "玩家不存在"}), 404

    player.is_ready = is_ready
    player.last_active_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "准备状态已更新",
        "data": {"is_ready": is_ready}
    })


@player_bp.route('/<int:player_id>', methods=['GET'])
def get_player(player_id):
    """获取玩家信息"""
    player = Player.query.get(player_id)

    if not player:
        return jsonify({"success": False, "error": "玩家不存在"}), 404

    return jsonify({
        "success": True,
        "data": player.to_dict()
    })
