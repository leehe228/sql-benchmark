# sql-benchmark/worker/Dockerfile

FROM ubuntu:22.04

# 1) 기본 패키지 설치
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    unixodbc unixodbc-dev \
    libpq-dev \
    curl \
    gnupg2

RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17

# 2) Python 패키지 설치
RUN pip3 install pandas sqlalchemy psycopg2-binary pyodbc pyyaml

# 3) 작업 디렉토리 설정 (임시)
WORKDIR /opt

# 4) GitHub에서 sql-benchmark 레포지토리 clone
RUN git clone https://github.com/leehe228/sql-benchmark.git

# 5) 이후 작업 디렉토리를 sql-benchmark로 이동
WORKDIR /opt/sql-benchmark

# 6) 컨테이너 실행 시 run_benchmark.py 실행
CMD ["python3", "worker/run_benchmark.py"]
