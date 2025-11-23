-- 更新产品配方表的难度值（从1-3改为3-5）
-- 奶茶、椰奶、柠檬茶、果汁: 难度1 → 3 (需掷骰 >= 2, 83%成功率)
-- 珍珠奶茶、水果奶昔: 难度2 → 4 (需掷骰 >= 3, 67%成功率)
-- 水果茶: 难度3 → 5 (需掷骰 >= 4, 50%成功率)

UPDATE `product_recipes` SET `difficulty` = 3 WHERE `name` = '奶茶';
UPDATE `product_recipes` SET `difficulty` = 3 WHERE `name` = '椰奶';
UPDATE `product_recipes` SET `difficulty` = 3 WHERE `name` = '柠檬茶';
UPDATE `product_recipes` SET `difficulty` = 3 WHERE `name` = '果汁';
UPDATE `product_recipes` SET `difficulty` = 4 WHERE `name` = '珍珠奶茶';
UPDATE `product_recipes` SET `difficulty` = 4 WHERE `name` = '水果奶昔';
UPDATE `product_recipes` SET `difficulty` = 5 WHERE `name` = '水果茶';

-- 验证更新结果
SELECT id, name, difficulty, base_fan_rate, recipe_json FROM `product_recipes` ORDER BY id;
