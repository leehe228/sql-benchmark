SELECT `spree_orders`.* FROM `spree_orders` INNER JOIN `spree_shipments` ON `spree_orders`.`id` = `spree_shipments`.`order_id` WHERE `spree_shipments`.`id` = 198 LIMIT 1