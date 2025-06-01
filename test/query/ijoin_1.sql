SELECT d.name      AS dept_name,
       e.id        AS emp_id,
       e.name      AS emp_name
FROM departments d
INNER JOIN employees e
ON d.id = e.dept_id;