"""
游戏常量定义
"""


class GameConstants:
    """游戏常量"""

    # 游戏基础
    TOTAL_ROUNDS = 10
    INITIAL_CASH = 10000.0
    MAX_PLAYERS = 4
    MIN_PLAYERS = 2

    # 店铺装修
    DECORATION_COSTS = {
        1: 400,   # 简装
        2: 800,   # 精装
        3: 1600   # 豪华装
    }

    MAX_EMPLOYEES = {
        1: 2,  # 简装容纳2人
        2: 3,  # 精装容纳3人
        3: 4   # 豪华装容纳4人
    }

    # 原材料价格（每份单价，基于每10份的包装价格）
    MATERIAL_BASE_PRICES = {
        "tea": 6.0,        # 60元/10份 = 6元/份
        "milk": 4.0,       # 40元/10份 = 4元/份
        "fruit": 5.0,      # 50元/10份 = 5元/份
        "ingredient": 2.0  # 20元/10份 = 2元/份
    }

    # 市场行动费用
    MARKET_RESEARCH_COST = 500
    ADVERTISEMENT_COST = 800
    PRODUCT_RESEARCH_COST = 600

    # 定价规则
    MIN_PRICE = 10
    MAX_PRICE = 40
    PRICE_STEP = 5

    # 固定客流量脚本（10回合）
    # 来源：user_jiagou.md 客流脚本表
    CUSTOMER_FLOW_SCRIPT = {
        1:  {"high": 40,  "low": 300},
        2:  {"high": 90,  "low": 280},
        3:  {"high": 110, "low": 330},
        4:  {"high": 60,  "low": 200},
        5:  {"high": 70,  "low": 280},
        6:  {"high": 120, "low": 250},
        7:  {"high": 160, "low": 330},
        8:  {"high": 40,  "low": 430},
        9:  {"high": 80,  "low": 260},
        10: {"high": 190, "low": 610}
    }

    # 批量折扣
    DISCOUNT_PER_TIER = 0.1  # 每50份-10%
    DISCOUNT_TIER_SIZE = 50
    MAX_DISCOUNT_TIERS = 5   # 最多5次折扣（-50%）

    # 产品配方数据
    # 难度3（简单）：需要掷骰 >= 2，成功率83%
    # 难度4（中等）：需要掷骰 >= 3，成功率67%
    # 难度5（困难）：需要掷骰 >= 4，成功率50%
    PRODUCT_RECIPES = [
        {
            "name": "奶茶",
            "difficulty": 3,
            "base_fan_rate": 5.0,
            "cost_per_unit": 10.0,
            "recipe_json": {"milk": 1, "tea": 1}
        },
        {
            "name": "椰奶",
            "difficulty": 3,
            "base_fan_rate": 5.0,
            "cost_per_unit": 9.0,
            "recipe_json": {"milk": 1, "fruit": 1}
        },
        {
            "name": "柠檬茶",
            "difficulty": 3,
            "base_fan_rate": 5.0,
            "cost_per_unit": 11.0,
            "recipe_json": {"tea": 1, "fruit": 1}
        },
        {
            "name": "果汁",
            "difficulty": 3,
            "base_fan_rate": 5.0,
            "cost_per_unit": 10.0,
            "recipe_json": {"fruit": 2}
        },
        {
            "name": "珍珠奶茶",
            "difficulty": 4,
            "base_fan_rate": 20.0,
            "cost_per_unit": 16.0,
            "recipe_json": {"milk": 2, "tea": 1, "ingredient": 1}
        },
        {
            "name": "水果奶昔",
            "difficulty": 4,
            "base_fan_rate": 20.0,
            "cost_per_unit": 15.0,
            "recipe_json": {"milk": 1, "fruit": 1, "ingredient": 3}
        },
        {
            "name": "水果茶",
            "difficulty": 5,
            "base_fan_rate": 30.0,
            "cost_per_unit": 23.0,
            "recipe_json": {"fruit": 3, "tea": 1, "ingredient": 1}
        }
    ]
