SELECT DEPT0.NAME, MAX(DEPT0.NAME), SUM(DEPT0.DEPTNO) / COUNT(*), MIN(DEPT0.NAME) FROM DEPT AS DEPT0 GROUP BY DEPT0.NAME
