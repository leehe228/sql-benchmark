SELECT DATE_TRUNC('month', o.order_date) AS month,
       p.product_name,
       SUM(oi.quantity * oi.unit_price)  AS monthly_sales
FROM orders o
JOIN order_items oi ON o.order_id   = oi.order_id
JOIN products    p  ON oi.product_id = p.product_id
GROUP BY month, p.product_name
ORDER BY month, p.product_name;