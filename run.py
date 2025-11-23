"""
Flask应用启动脚本
"""
import os
from app.main import app

if __name__ == '__main__':
    # 从环境变量读取端口，Zeabur 部署时会设置 PORT 环境变量
    port = int(os.getenv('PORT', 8000))
    debug = os.getenv('DEBUG', 'False') == 'True'

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
