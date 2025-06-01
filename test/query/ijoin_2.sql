SELECT o.order_id,
       p.product_name,
       oi.quantity,
       oi.quantity * oi.unit_price AS line_total
FROM orders o
INNER JOIN order_items oi  ON o.order_id = oi.order_id
INNER JOIN products    p   ON oi.product_id = p.product_id;