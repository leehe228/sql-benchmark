#!/usr/bin/env python3
# sql-benchmark/worker/run_benchmark.py

import os
import time
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
        return (f"mssql+pyodbc://{db_user}:{db_pass}@{db_host}:{db_port}/"
                f"{db_name}?driver=ODBC+Driver+17+for+SQL+Server;TrustServerCertificate=yes")
    elif db_type == "sqlite":
        return f"sqlite:///{db_name}.db"
    else:
        raise ValueError(f"Unsupported DB_TYPE: {db_type}")

def load_query(benchmark, query_number):
    """
    벤치마크 폴더에서 query_number.sql 파일을 읽어온다.
    """
    db_type = os.environ.get("DB_TYPE", "mssql").lower()
    query_path = f"/opt/sql-benchmark/{benchmark}/{db_type}/{query_number}.sql"
    if not os.path.exists(query_path):
        query_path = f"/opt/sql-benchmark/{benchmark}/{query_number}.sql"
    with open(query_path, "r", encoding="utf-8") as f:
        return f.read()

def wait_for_db(engine, timeout=180):
    """
    DB가 완전히 준비될 때까지 연결 시도를 반복.
    """
    start_time = time.time()
    while True:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("DB is ready.")
            break
        except Exception as e:
            if time.time() - start_time > timeout:
                raise Exception("Timeout waiting for DB readiness.")
            print("Waiting for DB to be ready...")
            time.sleep(2)

def execute_query_with_retry(engine, query, retries=3, delay=30):
    """
    쿼리 실행에 실패하면 일정 횟수 재시도한다.
    """
    attempt = 0
    while attempt < retries:
        try:
            start_time = time.time()
            with engine.connect() as conn:
                conn.execute(text(query))
            return time.time() - start_time
        except Exception as e:
            attempt += 1
            print(f"Attempt {attempt}/{retries} failed: {e}")
            time.sleep(delay)
    raise Exception(f"Query execution failed after {retries} attempts.")

def main():
    # 환경변수로 설정값 읽기
    db_type      = os.environ.get("DB_TYPE", "postgres")
    benchmark    = os.environ.get("BENCHMARK", "tpch").lower()
    query_start  = int(os.environ.get("QUERY_START", "1"))
    query_end    = int(os.environ.get("QUERY_END", "10"))
    repeat_count = int(os.environ.get("REPEAT_COUNT", "10"))
    output_csv   = os.environ.get("RESULT_CSV", "/mnt/results/benchmark_results.csv")
    log_file     = os.environ.get("RESULT_LOG", "/mnt/results/benchmark.log")

    os.makedirs("/mnt/results", exist_ok=True)

    conn_str = get_connection_string()
    engine = sqlalchemy.create_engine(conn_str)

    # DB 준비 대기
    wait_for_db(engine, timeout=60)

    results = []

    def write_log(msg):
        with open(log_file, "a", encoding="utf-8") as lf:
            lf.write(msg + "\n")

    write_log(f"=== Starting benchmark={benchmark}, DB={db_type}, queries={query_start}~{query_end}, repeat={repeat_count} ===")

    for qnum in range(query_start, query_end + 1):
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
            error_text = ""
            try:
                elapsed = execute_query_with_retry(engine, query, retries=3, delay=3)
                msg = f"Query {qnum}, run {run_idx}: {elapsed:.3f} sec"
                print(msg)
                write_log(msg)
            except Exception as ex:
                elapsed = None
                error_text = str(ex)
                err_log = f"[ERROR] Query {qnum}, run {run_idx}: {ex}"
                print(err_log)
                write_log(err_log)
            results.append({
                "benchmark": benchmark,
                "db_type": db_type,
                "query_number": qnum,
                "run_idx": run_idx,
                "elapsed_sec": elapsed,
                "error": error_text
            })

    results_df = pd.DataFrame(results)
    results_df.to_csv(output_csv, index=False)
    done_msg = f"\nAll done! Results saved to {output_csv}\n"
    print(done_msg)
    write_log(done_msg)

if __name__ == "__main__":
    main()