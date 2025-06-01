SELECT e.id, e.name, d.name AS dept_name
FROM employees e
LEFT JOIN departments d
ON e.dept_id = d.id;