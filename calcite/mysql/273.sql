SELECT EMP.DEPTNO, DEPT.DEPTNO AS DEPTNO0 FROM EMP AS EMP INNER JOIN DEPT AS DEPT ON EMP.DEPTNO = DEPT.DEPTNO GROUP BY EMP.DEPTNO, DEPT.DEPTNO
