SELECT s.student_id,
       s.name        AS student_name,
       c.course_code,
       c.title       AS course_title
FROM students       s
INNER JOIN enroll   e ON s.student_id = e.student_id
INNER JOIN courses  c ON e.course_id  = c.course_id;