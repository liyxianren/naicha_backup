-- ============================================
-- 奶茶大作战 - 数据库初始化脚本 (MySQL版本)
-- ============================================

-- 设置字符集
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================
-- 1. 游戏房间表 (games)
-- ============================================
DROP TABLE IF EXISTS `games`;
CREATE TABLE `games` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `room_code` VARCHAR(6) UNIQUE NOT NULL COMMENT '房间号',
    `status` VARCHAR(20) NOT NULL DEFAULT 'waiting' COMMENT '游戏状态: waiting, playing, finished',
    `current_round` INT DEFAULT 1 COMMENT '当前回合',
    `max_players` INT DEFAULT 4 COMMENT '最大玩家数',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `started_at` TIMESTAMP NULL,
    `finished_at` TIMESTAMP NULL,
    `settings` JSON COMMENT '游戏设置',
    INDEX `idx_room_code` (`room_code`),
    INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='游戏房间表';

-- ============================================
-- 2. 玩家表 (players)
-- ============================================
DROP TABLE IF EXISTS `players`;
CREATE TABLE `players` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `game_id` INT NOT NULL COMMENT '游戏ID',
    `nickname` VARCHAR(50) NOT NULL COMMENT '玩家昵称',
    `player_number` INT NOT NULL COMMENT '玩家编号 (1-4)',
    `cash` DECIMAL(10, 2) DEFAULT 10000.00 COMMENT '现金余额',
    `total_profit` DECIMAL(10, 2) DEFAULT 0.00 COMMENT '累计利润',
    `is_ready` BOOLEAN DEFAULT FALSE COMMENT '是否准备',
    `is_active` BOOLEAN DEFAULT TRUE COMMENT '是否在线',
    `joined_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `uk_game_player` (`game_id`, `player_number`),
    INDEX `idx_game_player` (`game_id`, `player_number`),
    FOREIGN KEY (`game_id`) REFERENCES `games`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='玩家表';

-- ============================================
-- 3. 店铺表 (shops)
-- ============================================
DROP TABLE IF EXISTS `shops`;
CREATE TABLE `shops` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `player_id` INT NOT NULL COMMENT '玩家ID',
    `location` VARCHAR(50) COMMENT '店铺位置',
    `rent` DECIMAL(8, 2) COMMENT '每回合租金',
    `decoration_level` INT DEFAULT 0 COMMENT '装修等级: 0=无, 1=简装, 2=精装, 3=豪华',
    `max_employees` INT DEFAULT 0 COMMENT '最大员工数',
    `created_round` INT NOT NULL COMMENT '开店回合',
    UNIQUE KEY `uk_player` (`player_id`),
    FOREIGN KEY (`player_id`) REFERENCES `players`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='店铺表';

-- ============================================
-- 4. 产品配方表 (product_recipes) - 配置表
-- ============================================
DROP TABLE IF EXISTS `product_recipes`;
CREATE TABLE `product_recipes` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(50) UNIQUE NOT NULL COMMENT '产品名称',
    `difficulty` INT NOT NULL COMMENT '研发难度',
    `base_fan_rate` DECIMAL(5, 2) NOT NULL COMMENT '初始圈粉率 (%)',
    `cost_per_unit` DECIMAL(6, 2) NOT NULL COMMENT '单杯成本',
    `recipe_json` JSON NOT NULL COMMENT '配方 JSON',
    `is_active` BOOLEAN DEFAULT TRUE,
    INDEX `idx_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='产品配方表';

-- 插入7种产品配方
INSERT INTO `product_recipes` (`name`, `difficulty`, `base_fan_rate`, `cost_per_unit`, `recipe_json`) VALUES
('奶茶', 3, 5.00, 10.00, '{"tea": 1, "milk": 1}'),
('椰奶', 3, 5.00, 9.00, '{"milk": 1, "fruit": 1}'),
('柠檬茶', 3, 5.00, 11.00, '{"tea": 1, "fruit": 1}'),
('果汁', 3, 5.00, 10.00, '{"fruit": 2}'),
('珍珠奶茶', 4, 20.00, 16.00, '{"milk": 2, "tea": 1, "ingredient": 1}'),
('水果奶昔', 4, 20.00, 15.00, '{"milk": 1, "fruit": 1, "ingredient": 3}'),
('水果茶', 5, 30.00, 23.00, '{"fruit": 3, "tea": 1, "ingredient": 1}');

-- ============================================
-- 5. 玩家产品表 (player_products)
-- ============================================
DROP TABLE IF EXISTS `player_products`;
CREATE TABLE `player_products` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `player_id` INT NOT NULL COMMENT '玩家ID',
    `recipe_id` INT NOT NULL COMMENT '配方ID',
    `is_unlocked` BOOLEAN DEFAULT FALSE COMMENT '是否已解锁',
    `unlocked_round` INT COMMENT '解锁回合',
    `total_sold` INT DEFAULT 0 COMMENT '累计销售杯数',
    `current_price` DECIMAL(6, 2) COMMENT '当前定价',
    `current_ad_score` INT DEFAULT 0 COMMENT '当前广告分',
    UNIQUE KEY `uk_player_recipe` (`player_id`, `recipe_id`),
    INDEX `idx_player_product` (`player_id`, `recipe_id`),
    FOREIGN KEY (`player_id`) REFERENCES `players`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`recipe_id`) REFERENCES `product_recipes`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='玩家产品表';

-- ============================================
-- 6. 员工表 (employees)
-- ============================================
DROP TABLE IF EXISTS `employees`;
CREATE TABLE `employees` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `shop_id` INT NOT NULL COMMENT '店铺ID',
    `name` VARCHAR(50) NOT NULL COMMENT '员工姓名',
    `salary` DECIMAL(8, 2) NOT NULL COMMENT '工资',
    `productivity` INT NOT NULL COMMENT '生产力',
    `hired_round` INT NOT NULL COMMENT '招募回合',
    `is_active` BOOLEAN DEFAULT TRUE COMMENT '是否在职',
    INDEX `idx_shop` (`shop_id`),
    FOREIGN KEY (`shop_id`) REFERENCES `shops`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='员工表';

-- ============================================
-- 7. 回合生产计划表 (round_productions)
-- ============================================
DROP TABLE IF EXISTS `round_productions`;
CREATE TABLE `round_productions` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `player_id` INT NOT NULL COMMENT '玩家ID',
    `round_number` INT NOT NULL COMMENT '回合数',
    `product_id` INT NOT NULL COMMENT '产品ID (player_products.id)',
    `allocated_productivity` INT DEFAULT 0 COMMENT '分配的生产力',
    `price` DECIMAL(6, 2) COMMENT '定价',
    `produced_quantity` INT DEFAULT 0 COMMENT '生产数量',
    `sold_quantity` INT DEFAULT 0 COMMENT '实际销售数量',
    `sold_to_high_tier` INT DEFAULT 0 COMMENT '卖给高购买力客户数量',
    `sold_to_low_tier` INT DEFAULT 0 COMMENT '卖给低购买力客户数量',
    `revenue` DECIMAL(10, 2) DEFAULT 0.00 COMMENT '销售收入',
    UNIQUE KEY `uk_player_round_product` (`player_id`, `round_number`, `product_id`),
    INDEX `idx_round_prod` (`player_id`, `round_number`),
    FOREIGN KEY (`player_id`) REFERENCES `players`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='回合生产计划表';

-- ============================================
-- 8. 原材料库存表 (material_inventories)
-- ============================================
DROP TABLE IF EXISTS `material_inventories`;
CREATE TABLE `material_inventories` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `player_id` INT NOT NULL COMMENT '玩家ID',
    `round_number` INT NOT NULL COMMENT '回合数',
    `material_type` VARCHAR(20) NOT NULL COMMENT '原材料类型: tea, milk, fruit, ingredient',
    `quantity` INT DEFAULT 0 COMMENT '库存数量',
    `purchase_price` DECIMAL(8, 2) COMMENT '本回合采购单价',
    UNIQUE KEY `uk_player_round_material` (`player_id`, `round_number`, `material_type`),
    INDEX `idx_player_round` (`player_id`, `round_number`),
    FOREIGN KEY (`player_id`) REFERENCES `players`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='原材料库存表';

-- ============================================
-- 9. 财务记录表 (finance_records)
-- ============================================
DROP TABLE IF EXISTS `finance_records`;
CREATE TABLE `finance_records` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `player_id` INT NOT NULL COMMENT '玩家ID',
    `round_number` INT NOT NULL COMMENT '回合数',

    -- 收入
    `total_revenue` DECIMAL(10, 2) DEFAULT 0.00 COMMENT '总收入',
    `revenue_breakdown` JSON COMMENT '收入明细 JSON',

    -- 支出
    `rent_expense` DECIMAL(8, 2) DEFAULT 0.00 COMMENT '租金支出',
    `salary_expense` DECIMAL(8, 2) DEFAULT 0.00 COMMENT '工资支出',
    `material_expense` DECIMAL(8, 2) DEFAULT 0.00 COMMENT '原材料支出',
    `decoration_expense` DECIMAL(8, 2) DEFAULT 0.00 COMMENT '装修支出',
    `research_expense` DECIMAL(8, 2) DEFAULT 0.00 COMMENT '调研支出',
    `ad_expense` DECIMAL(8, 2) DEFAULT 0.00 COMMENT '广告支出',
    `research_cost` DECIMAL(8, 2) DEFAULT 0.00 COMMENT '研发支出',
    `total_expense` DECIMAL(10, 2) DEFAULT 0.00 COMMENT '总支出',

    -- 利润
    `round_profit` DECIMAL(10, 2) DEFAULT 0.00 COMMENT '本回合利润',
    `cumulative_profit` DECIMAL(10, 2) DEFAULT 0.00 COMMENT '累计利润',

    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `uk_player_round` (`player_id`, `round_number`),
    INDEX `idx_finance` (`player_id`, `round_number`),
    FOREIGN KEY (`player_id`) REFERENCES `players`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='财务记录表';

-- ============================================
-- 10. 客流量表 (customer_flows)
-- ============================================
DROP TABLE IF EXISTS `customer_flows`;
CREATE TABLE `customer_flows` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `game_id` INT NOT NULL COMMENT '游戏ID',
    `round_number` INT NOT NULL COMMENT '回合数',
    `high_tier_customers` INT NOT NULL COMMENT '高购买力客户数',
    `low_tier_customers` INT NOT NULL COMMENT '低购买力客户数',
    `generated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `uk_game_round` (`game_id`, `round_number`),
    INDEX `idx_game_round` (`game_id`, `round_number`),
    FOREIGN KEY (`game_id`) REFERENCES `games`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='客流量表';

-- ============================================
-- 11. 研发记录表 (research_logs)
-- ============================================
DROP TABLE IF EXISTS `research_logs`;
CREATE TABLE `research_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `player_id` INT NOT NULL COMMENT '玩家ID',
    `recipe_id` INT NOT NULL COMMENT '配方ID',
    `round_number` INT NOT NULL COMMENT '回合数',
    `dice_result` INT NOT NULL COMMENT '骰子点数',
    `success` BOOLEAN NOT NULL COMMENT '是否成功',
    `cost` DECIMAL(8, 2) DEFAULT 600.00 COMMENT '研发费用',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_player_round` (`player_id`, `round_number`),
    FOREIGN KEY (`player_id`) REFERENCES `players`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`recipe_id`) REFERENCES `product_recipes`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='研发记录表';

-- ============================================
-- 12. 市场行动表 (market_actions)
-- ============================================
DROP TABLE IF EXISTS `market_actions`;
CREATE TABLE `market_actions` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `player_id` INT NOT NULL COMMENT '玩家ID',
    `round_number` INT NOT NULL COMMENT '回合数',
    `action_type` VARCHAR(20) NOT NULL COMMENT '行动类型: ad (广告), research (调研)',
    `cost` DECIMAL(8, 2) NOT NULL COMMENT '费用',
    `result_value` INT COMMENT '结果值 (广告分等)',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_player_round` (`player_id`, `round_number`),
    FOREIGN KEY (`player_id`) REFERENCES `players`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='市场行动表';

-- ============================================
-- 完成
-- ============================================
SET FOREIGN_KEY_CHECKS = 1;

-- 查看创建的表
SHOW TABLES;
