"""
用户认证相关API
"""
from flask import Blueprint, request, jsonify
from app.core.database import db
from app.models.player import Player
from datetime import datetime, timedelta
import uuid

auth_bp = Blueprint('auth', __name__)


def _extract_session_token():
    """统一从 body/header/query 中提取 session_token。"""
    data = request.get_json(silent=True) or {}
    token = data.get('session_token')
    if not token:
        token = request.headers.get('X-Session-Token')
    if not token:
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '')
    if not token:
        token = request.args.get('session_token')
    return token


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录，生成 session_token
    请求体: { "nickname": "昵称" }
    响应: { "session_token": "...", "nickname": "..." }
    """
    data = request.get_json() or {}
    nickname = data.get('nickname', '').strip()

    if not nickname:
        return jsonify({"success": False, "error": "请填写昵称"}), 400

    if len(nickname) > 50:
        return jsonify({"success": False, "error": "昵称不能超过50个字符"}), 400

    session_token = str(uuid.uuid4())

    return jsonify({
        "success": True,
        "data": {
            "session_token": session_token,
            "nickname": nickname
        },
        "message": "登录成功"
    }), 200


@auth_bp.route('/heartbeat', methods=['POST'])
def heartbeat():
    """
    心跳接口 - 刷新 last_active_at
    请求体或头部: { "session_token": "..." }
    """
    session_token = _extract_session_token()

    if not session_token:
        return jsonify({"success": False, "error": "缺少 session_token"}), 400

    player = Player.query.filter_by(session_token=session_token).first()

    if not player:
        return jsonify({
            "success": True,
            "message": "心跳成功（尚未加入房间）"
        }), 200

    player.last_active_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        "success": True,
        "data": {
            "player_id": player.id,
            "game_id": player.game_id
        },
        "message": "心跳成功"
    }), 200


@auth_bp.route('/session', methods=['GET'])
def get_session():
    """
    根据 session_token 获取玩家信息
    可从 Header.Authorization/X-Session-Token 或 query/body 读取 token
    """
    session_token = _extract_session_token()

    if not session_token:
        return jsonify({"success": False, "error": "缺少 session_token"}), 400

    player = Player.query.filter_by(session_token=session_token).first()

    if not player:
        return jsonify({
            "success": False,
            "error": "未找到会话或已被清理"
        }), 404

    # 超过5分钟未活跃则认为过期
    if player.last_active_at:
        inactive_seconds = (datetime.utcnow() - player.last_active_at).total_seconds()
        if inactive_seconds > 300:
            return jsonify({
                "success": False,
                "error": "会话已过期（超过5分钟未活跃）"
            }), 401

    return jsonify({
        "success": True,
        "data": player.to_dict()
    }), 200
