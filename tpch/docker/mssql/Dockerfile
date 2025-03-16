FROM mcr.microsoft.com/mssql/server:2022-latest

# 1) 필수 환경변수 & 설정
ENV ACCEPT_EULA=Y
ENV MSSQL_SA_PASSWORD="Dlghdms0228" 
ENV MSSQL_PID=Developer

USER root
RUN apt-get update && apt-get install -y git make gcc python3 procps

# 2) 개인 깃허브 clone (TPC-H 수정 버전)
RUN git clone https://github.com/leehe228/TPC-H-Dataset-Generator-MS-SQL-Server /opt/tpch-dbgen
WORKDIR /opt/tpch-dbgen/dbgen

# 3) dbgen 컴파일 & 스케일 팩터=1 데이터 생성
RUN make
RUN ./dbgen -s 1

# 4) MSSQL 프로세스가 .tbl 파일 읽도록 권한 설정
RUN chown -R mssql:mssql /opt/tpch-dbgen && chmod -R 755 /opt/tpch-dbgen

# 5) 컨테이너 빌드 시점에 MS SQL 임시 실행 → DB 로드 및 tpch 데이터베이스 생성
USER mssql
RUN (/opt/mssql/bin/sqlservr &) \
    && echo "Waiting 20s for MS SQL to start..." \
    && sleep 20 \
    && echo "Checking SQL Server readiness..." \
    && for i in $(seq 1 30); do \
         /opt/mssql-tools18/bin/sqlcmd -S "tcp:localhost,1433" -U SA -P "Dlghdms0228" -C -Q "SELECT 1" && break || sleep 2; \
       done \
    && echo "Creating tpch database..." \
    && /opt/mssql-tools18/bin/sqlcmd -S "tcp:localhost,1433" -U SA -P "Dlghdms0228" -C -Q "CREATE DATABASE tpch;" \
    && echo "Loading TPC-H schema..." \
    && /opt/mssql-tools18/bin/sqlcmd -S "tcp:localhost,1433" -U SA -P "Dlghdms0228" -C -i /opt/tpch-dbgen/schema/tpch.sql \
    && echo "Loading TPC-H foreign key constraints..." \
    && /opt/mssql-tools18/bin/sqlcmd -S "tcp:localhost,1433" -U SA -P "Dlghdms0228" -C -i /opt/tpch-dbgen/schema/tpch_fk.sql \
    && pkill sqlservr \
    && echo "TPC-H setup completed at build time."

# 6) 컨테이너 실행 시 포트 개방 & sqlservr 실행
EXPOSE 1433
CMD ["/opt/mssql/bin/sqlservr"]