"""
添加玩家会话管理字段
为 players 表添加 session_token 和 last_active_at 字段
执行方式: python add_player_session.py
"""
import sys
import os
import io

# 设置标准输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pymysql

# 数据库连接信息
DB_CONFIG = {
    "host": "sfo1.clusters.zeabur.com",
    "port": 32206,
    "user": "root",
    "password": "I51dXb3JY6vgM87uf2SBsQ9W4yKRhOt0",
    "database": "zeabur",
    "charset": "utf8mb4"
}

def add_session_fields():
    """添加会话相关字段到 players 表"""
    print("连接数据库...")
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        # 添加 session_token 字段（唯一索引）
        print("添加 session_token 字段...")
        cursor.execute("""
            ALTER TABLE players
            ADD COLUMN session_token VARCHAR(100) UNIQUE NULL
            COMMENT '玩家会话令牌，用于身份认证'
        """)
        conn.commit()
        print("✓ session_token 字段添加成功")
    except Exception as e:
        if "Duplicate column name" in str(e):
            print("session_token 字段已存在，跳过")
        else:
            print(f"添加 session_token 字段失败: {e}")
        conn.rollback()

    try:
        # 添加 last_active_at 字段
        print("添加 last_active_at 字段...")
        cursor.execute("""
            ALTER TABLE players
            ADD COLUMN last_active_at TIMESTAMP NULL
            DEFAULT CURRENT_TIMESTAMP
            ON UPDATE CURRENT_TIMESTAMP
            COMMENT '最后活跃时间'
        """)
        conn.commit()
        print("✓ last_active_at 字段添加成功")
    except Exception as e:
        if "Duplicate column name" in str(e):
            print("last_active_at 字段已存在，跳过")
        else:
            print(f"添加 last_active_at 字段失败: {e}")
        conn.rollback()

    cursor.close()
    conn.close()
    print("\n数据库迁移完成！")

if __name__ == "__main__":
    add_session_fields()
