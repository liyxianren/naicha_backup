# 奶茶大作战 - 后端服务

基于 Flask + SQLAlchemy + MySQL 的游戏后端 API 服务。

## 技术栈

- **框架**: Flask 3.0
- **ORM**: SQLAlchemy 2.0
- **数据库**: MySQL (PyMySQL)
- **实时通信**: Flask-SocketIO
- **部署**: Docker + Zeabur

## 本地开发

### 环境要求

- Python 3.10+
- MySQL 数据库访问权限

### 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据库（首次运行）
python scripts/setup_database.py

# 启动开发服务器
python run.py
```

服务器将在 http://localhost:8000 启动。

### 环境变量配置

在 `backend/.env` 文件中配置：

```env
# 数据库连接
DATABASE_URL=mysql+pymysql://user:password@host:port/database

# Flask 配置
SECRET_KEY=your-secret-key
DEBUG=True

# CORS 配置
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

## 数据库管理

### 初始化数据库

```bash
python scripts/setup_database.py
```

这将创建所有 12 张表并初始化产品配方数据。

### 其他脚本

```bash
# 清空所有游戏数据（测试用）
python scripts/clear_all_games.py

# 添加玩家回合顺序字段
python scripts/add_turn_order.py

# 添加游戏名称字段
python scripts/add_game_name.py
```

## API 接口

### 主要端点

- `POST /api/v1/games/create` - 创建游戏房间
- `POST /api/v1/players/join/{room_code}` - 加入游戏
- `POST /api/v1/games/{room_code}/start` - 开始游戏
- `POST /api/v1/production/submit` - 提交生产决策
- `POST /api/v1/rounds/{game_id}/advance` - 推进回合
- `GET /api/v1/finance/game/{game_id}/profit-summary` - 获取利润排行

完整 API 文档：启动服务器后访问 `/docs` 端点

## 项目结构

```
backend/
├── app/
│   ├── api/v1/          # API 路由
│   ├── models/          # 数据模型（12张表）
│   ├── services/        # 业务逻辑层
│   ├── core/            # 核心配置
│   └── utils/           # 工具函数
├── scripts/             # 数据库脚本
├── tests/               # 单元测试
├── requirements.txt     # Python 依赖
├── run.py              # 启动脚本
├── Dockerfile          # Docker 构建文件
└── .dockerignore       # Docker 忽略文件
```

## Zeabur 部署

### 1. 准备工作

确保仓库包含：
- ✅ `Dockerfile` - Docker 构建配置
- ✅ `requirements.txt` - Python 依赖列表
- ✅ `run.py` - 启动脚本（支持 PORT 环境变量）

### 2. 部署步骤

1. 在 Zeabur 创建新项目
2. 添加服务 → 选择 Git 仓库
3. Zeabur 自动检测 Dockerfile 并构建

### 3. 环境变量配置

在 Zeabur 服务设置中添加以下环境变量：

```env
# 必需
DATABASE_URL=<Zeabur MySQL 连接字符串>
SECRET_KEY=<生产环境密钥>

# 推荐
DEBUG=False
FLASK_ENV=production
CORS_ORIGINS=https://your-frontend.zeabur.app

# 可选
DB_POOL_RECYCLE=300
```

### 4. 数据库配置

#### 方式 1：使用 Zeabur MySQL 服务

1. 在同一 Project 中添加 MySQL 服务
2. Zeabur 自动注入环境变量：
   - `MYSQL_USERNAME`
   - `MYSQL_PASSWORD`
   - `MYSQL_HOST`
   - `MYSQL_PORT`
   - `MYSQL_DATABASE`
   - `DATABASE_URL`（推荐直接使用）

#### 方式 2：使用外部数据库

手动配置 `DATABASE_URL`：
```
DATABASE_URL=mysql+pymysql://user:password@host:port/database
```

### 5. 初始化数据库

部署成功后，需要初始化数据库表：

```bash
# 通过 Zeabur Terminal 执行
python scripts/setup_database.py
```

### 6. 健康检查

访问 `https://your-backend.zeabur.app/health` 确认服务正常。

## 核心业务逻辑

### 三端架构

1. **生产端** - 玩家操作接口
   - 店铺管理、员工管理、产品研发、生产决策、市场行动

2. **计算端** - 游戏引擎
   - 口碑分计算、客流分配算法、批量折扣计算

3. **财务端** - 自动报表
   - 收支记录、利润统计、排行榜

### 关键算法

**口碑分计算：**
```python
口碑分 = 广告分 + (动态圈粉率 × 累计销售数)
动态圈粉率 = 基础圈粉率 - (解锁人数-1) × 5%
```

**客流分配：**
- 高购买力客户：优先口碑分，相同口碑看价格
- 低购买力客户：优先价格（口碑>0），相同价格看口碑

详见 `app/services/calculation_engine.py`

## 测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_customer_flow_allocator.py
```

## 注意事项

1. **端口配置**：生产环境必须使用 `PORT` 环境变量
2. **数据库连接**：使用 `pool_pre_ping=True` 防止连接超时
3. **CORS 设置**：确保允许前端域名跨域访问
4. **密钥安全**：生产环境使用强随机 `SECRET_KEY`
5. **调试模式**：生产环境必须设置 `DEBUG=False`

## License

MIT
