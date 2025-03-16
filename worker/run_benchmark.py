#!/usr/bin/env python3
# sql-benchmark/worker/run_benchmark.py

import os
import time
import csv
import sqlalchemy
from sqlalchemy import text
import pandas as pd

def get_connection_string():
    """
    환경변수로부터 DB 접속 정보를 읽어 SQLAlchemy용 접속 문자열을 반환.
    """
    db_type = os.environ.get("DB_TYPE", "postgres").lower()
    db_host = os.environ.get("DB_HOST", "dbms_container")
    db_port = os.environ.get("DB_PORT", "5432")
    db_name = os.environ.get("DB_NAME", "tpch")
    db_user = os.environ.get("DB_USER", "postgres")
    db_pass = os.environ.get("DB_PASS", "postgres")

    if db_type in ("postgres", "postgresql"):
        return f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    elif db_type in ("mssql", "ms sql server"):
        # ODBC Driver 17 or 18 for SQL Server가 설치되어 있어야 함
        return (f"mssql+pyodbc://{db_user}:{db_pass}@{db_host}:{db_port}/"
                f"{db_name}?driver=ODBC+Driver+17+for+SQL+Server")
    elif db_type == "sqlite":
        # SQLite 파일 DB. DB_NAME이 파일명으로 사용된다고 가정
        return f"sqlite:///{db_name}.db"
    else:
        raise ValueError(f"Unsupported DB_TYPE: {db_type}")

def load_query(benchmark, query_number):
    """
    벤치마크 폴더(예: job, tpch, stats, etc.)에서 query_number.sql 파일을 읽어온다.
    예: sql-benchmark/tpch/mssql/1.sql
    구조에 맞게 경로를 조정해야 함.
    """
    db_type = os.environ.get("DB_TYPE", "mssql").lower()
    query_path = f"/opt/sql-benchmark/{benchmark}/{db_type}/{query_number}.sql"

    if not os.path.exists(query_path):
        # fallback: sql-benchmark/<benchmark>/<query_number>.sql
        query_path = f"/opt/sql-benchmark/{benchmark}/{query_number}.sql"

    with open(query_path, "r", encoding="utf-8") as f:
        return f.read()

def main():
    # 환경변수로 설정값 읽기
    db_type      = os.environ.get("DB_TYPE", "postgres")
    benchmark    = os.environ.get("BENCHMARK", "tpch").lower()  # tpch, job, stats, ...
    query_start  = int(os.environ.get("QUERY_START", "1"))
    query_end    = int(os.environ.get("QUERY_END", "10"))
    repeat_count = int(os.environ.get("REPEAT_COUNT", "10"))

    # 결과 파일(덮어쓰기 방지)
    output_csv = os.environ.get("RESULT_CSV", "/mnt/results/benchmark_results.csv")
    # 로그 파일
    log_file = os.environ.get("RESULT_LOG", "/mnt/results/benchmark.log")

    os.makedirs("/mnt/results", exist_ok=True)

    # DB 연결
    conn_str = get_connection_string()
    engine = sqlalchemy.create_engine(conn_str)

    results = []

    # 로그 파일에 기록하는 헬퍼 함수
    def write_log(msg):
        with open(log_file, "a", encoding="utf-8") as lf:
            lf.write(msg + "\n")

    write_log(f"=== Starting benchmark={benchmark}, DB={db_type}, queries={query_start}~{query_end}, repeat={repeat_count} ===")

    for qnum in range(query_start, query_end + 1):
        # 쿼리 로드
        try:
            query = load_query(benchmark, qnum)
        except Exception as e:
            err_msg = f"[ERROR] Failed to load query {qnum}: {e}"
            print(err_msg)
            write_log(err_msg)
            continue

        log_msg = f"Running {benchmark} Query {qnum} for {repeat_count} runs..."
        print(log_msg)
        write_log(log_msg)

        for run_idx in range(1, repeat_count + 1):
            start_time = time.time()
            error_msg = ""
            try:
                with engine.connect() as conn:
                    conn.execute(text(query))
                elapsed = time.time() - start_time
                msg = f"Query {qnum}, run {run_idx}: {elapsed:.3f} sec"
                print(msg)
                write_log(msg)
            except Exception as ex:
                elapsed = None
                error_msg = str(ex)
                err_log = f"[ERROR] Query {qnum}, run {run_idx}: {ex}"
                print(err_log)
                write_log(err_log)

            results.append({
                "benchmark": benchmark,
                "db_type": db_type,
                "query_number": qnum,
                "run_idx": run_idx,
                "elapsed_sec": elapsed,
                "error": error_msg
            })

    # 결과를 CSV로 저장
    results_df = pd.DataFrame(results)
    results_df.to_csv(output_csv, index=False)
    done_msg = f"\nAll done! Results saved to {output_csv}\n"
    print(done_msg)
    write_log(done_msg)

if __name__ == "__main__":
    main()