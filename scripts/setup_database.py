"""
数据库初始化脚本
执行方式: python setup_database.py
"""
import sys
import os
import io

# 设置标准输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymysql
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据库连接信息
DB_CONFIG = {
    "host": "sfo1.clusters.zeabur.com",
    "port": 32206,
    "user": "root",
    "password": "I51dXb3JY6vgM87uf2SBsQ9W4yKRhOt0",
    "database": "zeabur",
    "charset": "utf8mb4"
}


def execute_sql_file(cursor, filepath):
    """执行SQL文件"""
    print(f"📄 正在执行SQL文件: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # 分割SQL语句（按分号分割，但跳过注释）
    statements = []
    current_statement = []

    for line in sql_content.split('\n'):
        # 跳过注释行
        if line.strip().startswith('--') or line.strip().startswith('/*'):
            continue

        # 跳过空行
        if not line.strip():
            continue

        current_statement.append(line)

        # 如果行以分号结尾，说明是一条完整的SQL语句
        if line.strip().endswith(';'):
            statement = '\n'.join(current_statement)
            statements.append(statement)
            current_statement = []

    # 执行每条SQL语句
    success_count = 0
    error_count = 0

    for i, statement in enumerate(statements, 1):
        statement = statement.strip()
        if not statement:
            continue

        try:
            cursor.execute(statement)
            success_count += 1

            # 显示简要信息
            if 'CREATE TABLE' in statement.upper():
                table_name = statement.split('`')[1]
                print(f"  ✓ 创建表: {table_name}")
            elif 'INSERT INTO' in statement.upper():
                table_name = statement.split('`')[1]
                print(f"  ✓ 插入数据到: {table_name}")
            elif 'DROP TABLE' in statement.upper():
                print(f"  ✓ 删除已存在的表")

        except Exception as e:
            error_count += 1
            print(f"  ✗ 错误 (语句 {i}): {str(e)[:100]}")

    print(f"\n📊 执行完成: 成功 {success_count} 条, 失败 {error_count} 条\n")
    return success_count, error_count


def main():
    """主函数"""
    print("=" * 60)
    print("🎮 奶茶大作战 - 数据库初始化")
    print("=" * 60)

    try:
        # 连接数据库
        print(f"\n🔌 正在连接数据库: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        connection = pymysql.connect(**DB_CONFIG)
        print("✓ 数据库连接成功!\n")

        cursor = connection.cursor()

        # 执行SQL初始化脚本
        sql_file = os.path.join(os.path.dirname(__file__), 'init_database.sql')
        success_count, error_count = execute_sql_file(cursor, sql_file)

        # 提交事务
        connection.commit()
        print("✓ 数据库初始化完成!\n")

        # 查询创建的表
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        print("📋 已创建的数据表:")
        for i, (table,) in enumerate(tables, 1):
            cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
            count = cursor.fetchone()[0]
            print(f"  {i}. {table:<25} ({count} 行)")

        print("\n" + "=" * 60)
        print("✅ 数据库初始化成功!")
        print("=" * 60)

    except pymysql.MySQLError as e:
        print(f"\n❌ 数据库错误: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()
            print("\n🔌 数据库连接已关闭")


if __name__ == "__main__":
    main()
