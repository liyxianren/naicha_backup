"""
执行 SQL 脚本更新产品配方数据
"""
import pymysql
import os

# 数据库配置（从环境变量读取，如果没有则使用默认值）
DB_CONFIG = {
    'host': 'db.zeabur.internal',
    'port': 3306,
    'user': 'root',
    'password': 'YO3MQxPb6kXiBUIl7KSfXEQQEQBo1M0c',
    'database': 'zeabur',
    'charset': 'utf8mb4'
}

def main():
    print("=" * 60)
    print("Starting to update product recipes...")
    print("=" * 60)

    try:
        # 连接数据库
        print(f"\nConnecting to database: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        connection = pymysql.connect(**DB_CONFIG)
        print("Database connected successfully!\n")

        cursor = connection.cursor()

        # 读取 SQL 文件
        sql_file = os.path.join(os.path.dirname(__file__), 'update_recipes.sql')
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # 分割并执行每个SQL语句
        sql_statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]

        for sql in sql_statements:
            if sql.upper().startswith('SELECT'):
                cursor.execute(sql)
                results = cursor.fetchall()
                print("\nCurrent product recipes:")
                for row in results:
                    print(f"  {row[0]}. {row[1]:<8} - Difficulty {row[2]} - Fan rate {row[3]}% - Recipe {row[4]}")
            else:
                cursor.execute(sql)
                print(f"Success: {sql[:50]}...")

        # 提交事务
        connection.commit()

        print("\n" + "=" * 60)
        print("Product recipes updated successfully!")
        print("=" * 60)

    except pymysql.MySQLError as e:
        print(f"\nDatabase error: {e}")
        return 1

    except Exception as e:
        print(f"\nError occurred: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()
            print("\nDatabase connection closed")

    return 0

if __name__ == "__main__":
    exit(main())
