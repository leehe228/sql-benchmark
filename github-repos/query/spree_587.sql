SELECT COUNT(*) FROM (SELECT 1 AS one FROM `spree_taxons` WHERE `spree_taxons`.`parent_id` = 17 ORDER BY `spree_taxons`.`lft` ASC LIMIT 25 OFFSET 0) subquery_for_count