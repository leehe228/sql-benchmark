SELECT c.customer_id,
       o.order_id,
       o.order_date
FROM customers c
LEFT JOIN orders o
  ON c.customer_id = o.customer_id
 AND o.status = 'shipped';