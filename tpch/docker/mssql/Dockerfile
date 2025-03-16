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

# 5) 컨테이너 빌드 시점에 MS SQL 임시 실행 → DB 로드
USER mssql

# 5-1) sqlservr를 백그라운드로 띄우고, 잠시 대기 후 TPC-H 로딩
RUN (/opt/mssql/bin/sqlservr &) \
    && echo "Waiting 20s for MS SQL to start..." \
    && sleep 20 \
    \
    # (가정) tpch.sql 안에 CREATE DATABASE tpch; 문, 그리고 BULK INSERT 로직이 포함
    && /opt/mssql-tools18/bin/sqlcmd \
         -S localhost \
         -U SA \
         -P "Dlghdms0228" \
         -N -C \
         -i /opt/tpch-dbgen/schema/tpch.sql \
    \
    && /opt/mssql-tools18/bin/sqlcmd \
         -S localhost \
         -U SA \
         -P "Dlghdms0228" \
         -N -C \
         -i /opt/tpch-dbgen/schema/tpch_fk.sql \
    \
    # 임시 서버 종료
    && pkill sqlservr \
    && echo "TPC-H setup completed at build time."

# 6) 컨테이너 실행 시 포트 개방 & sqlservr 실행
EXPOSE 1433
CMD ["/opt/mssql/bin/sqlservr"]
