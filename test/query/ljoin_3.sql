SELECT p.post_id,
       p.title,
       COUNT(c.comment_id) AS comment_cnt
FROM posts p
LEFT JOIN comments c
  ON p.post_id = c.post_id
GROUP BY p.post_id, p.title;