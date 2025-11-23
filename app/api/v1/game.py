"""
游戏房间 API (Flask Blueprint)
"""
from flask import Blueprint, request, jsonify
from app.core.database import db
from app.models.game import Game, CustomerFlow
from app.models.player import Player
from datetime import datetime
import random
import string

# 蓝图
game_bp = Blueprint('games', __name__)


def generate_room_code(length=6):
    """生成房间代码"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def _extract_session_token(data: dict):
    """优先取 body，其次请求头/Authorization"""
    token = data.get('session_token')
    if not token:
        token = request.headers.get('X-Session-Token')
    if not token:
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '')
    return token


@game_bp.route('', methods=['POST'])
def create_game():
    """创建游戏房间并自动加入"""
    data = request.get_json() or {}
    game_name = data.get('name', '奶茶房间')
    max_players = data.get('max_players', 4)
    session_token = _extract_session_token(data)
    player_name = data.get('player_name')  # 玩家昵称，来自登录

    if not session_token:
        return jsonify({"success": False, "error": "请先登录"}), 401

    if not player_name:
        return jsonify({"success": False, "error": "请输入玩家昵称"}), 400

    # 若当前 session 已绑定旧房间，视为重新开房：删除旧玩家，房间无玩家则清理
    existing_player = Player.query.filter_by(session_token=session_token).first()
    if existing_player:
        old_game_id = existing_player.game_id
        db.session.delete(existing_player)
        db.session.commit()

        if old_game_id:
            remaining = Player.query.filter_by(game_id=old_game_id).count()
            if remaining == 0:
                old_game = Game.query.get(old_game_id)
                if old_game:
                    db.session.delete(old_game)
                    db.session.commit()

    # 生成唯一房间码
    while True:
        room_code = generate_room_code()
        existing = Game.query.filter_by(room_code=room_code).first()
        if not existing:
            break

    # 创建游戏
    game = Game(
        name=game_name,
        room_code=room_code,
        status='waiting',
        max_players=max_players,
        current_round=1
    )

    db.session.add(game)
    db.session.flush()  # 获取game.id

    # 自动创建玩家并加入房间
    from app.models.product import ProductRecipe, PlayerProduct

    player = Player(
        game_id=game.id,
        nickname=player_name,
        player_number=1,
        turn_order=0,  # 房主=第一位玩家
        cash=10000.00,
        total_profit=0.00,
        is_ready=False,
        session_token=session_token,
        last_active_at=datetime.utcnow()
    )

    db.session.add(player)
    db.session.flush()  # 获取player.id

    # 初始化玩家配方（全部锁定）
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
        "data": {
            "game": game.to_dict(),
            "player": player.to_dict()
        }
    }), 201


@game_bp.route('/<int:game_id>', methods=['GET'])
def get_game(game_id):
    """获取游戏信息"""
    game = Game.query.get(game_id)

    if not game:
        return jsonify({"success": False, "error": "游戏房间不存在"}), 404

    return jsonify({
        "success": True,
        "data": game.to_dict()
    })


@game_bp.route('/<int:game_id>/players', methods=['GET'])
def get_game_players(game_id):
    """获取游戏玩家列表"""
    game = Game.query.get(game_id)

    if not game:
        return jsonify({"success": False, "error": "游戏房间不存在"}), 404

    players = Player.query.filter_by(game_id=game.id).all()

    return jsonify({
        "success": True,
        "data": [p.to_dict() for p in players]
    })


@game_bp.route('/<int:game_id>/start', methods=['POST'])
def start_game(game_id):
    """开始游戏"""
    game = Game.query.get(game_id)

    if not game:
        return jsonify({"success": False, "error": "游戏房间不存在"}), 404

    if game.status != 'waiting':
        return jsonify({"success": False, "error": "游戏已经开始"}), 400

    # 至少2名玩家
    player_count = Player.query.filter_by(game_id=game.id).count()
    if player_count < 2:
        return jsonify({"success": False, "error": "至少需要2名玩家"}), 400

    # 更新游戏状态
    game.status = 'in_progress'
    game.started_at = datetime.utcnow()

    # 生成所有回合的客流（固定脚本）
    from app.utils.game_constants import GameConstants
    for round_num in range(1, 11):  # 10回合
        flow_data = GameConstants.CUSTOMER_FLOW_SCRIPT.get(round_num, {"high": 40, "low": 300})

        customer_flow = CustomerFlow(
            game_id=game.id,
            round_number=round_num,
            high_tier_customers=flow_data["high"],
            low_tier_customers=flow_data["low"]
        )
        db.session.add(customer_flow)

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "游戏已开始",
        "data": {
            "status": "in_progress",
            "started_at": game.started_at.isoformat()
        }
    })


@game_bp.route('', methods=['GET'])
def list_games():
    """列出游戏房间"""
    status = request.args.get('status')

    query = Game.query

    if status:
        query = query.filter_by(status=status)

    games = query.all()

    return jsonify({
        "success": True,
        "data": [g.to_dict() for g in games]
    })
