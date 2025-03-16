#!/usr/bin/env python3
# sql-benchmark/scheduler.py

import os
import time
import subprocess
import yaml  # pip install pyyaml
from collections import deque
import argparse

class Batch:
    def __init__(self, batch_id, benchmark, query_start, query_end, db_type, repeat_count):
        self.batch_id = batch_id
        self.benchmark = benchmark
        self.query_start = query_start
        self.query_end = query_end
        self.db_type = db_type
        self.repeat_count = repeat_count
        self.status = "queued"
        # compose 파일명
        self.compose_file = f"compose_batch_{batch_id}.yml"
        # 결과 CSV 경로
        self.result_csv = f"results/batch_{batch_id}.csv"

    def __str__(self):
        return (f"[Batch {self.batch_id}] {self.benchmark} Q{self.query_start}-{self.query_end} "
                f"DB={self.db_type}, repeat={self.repeat_count}, status={self.status}")

def generate_compose_file(batch: Batch):
    """
    외부 접근 없이 worker와 dbms 컨테이너끼리 내부 네트워크로 통신하도록 docker-compose.yml 파일을 생성.
    컨테이너 이름을 알아보기 쉽게 db_type, benchmark, 쿼리 범위, batch_id 등을 포함.
    Worker 컨테이너에 RESULT_CSV, RESULT_LOG 환경변수를 전달하여,
    배치별로 다른 CSV/로그 파일을 사용하도록 설정.
    """
    db_image_map = {
        "postgres": "hoeunlee228/postgres-tpch:latest",
        "mssql":    "hoeunlee228/mssql-tpch:latest"
    }
    db_image = db_image_map.get(batch.db_type.lower(), "hoeunlee228/postgres-tpch:latest")

    # 내부 포트만 사용 (외부 노출 없음)
    if batch.db_type.lower() == "mssql":
        container_port = "1433"
        db_user = "SA"
        db_pass = "Dlghdms0228"
    else:
        container_port = "5432"
        db_user = "postgres"
        db_pass = "postgres"

    # 컨테이너 이름을 직관적으로 구성
    db_container_name = f"db_{batch.db_type}_{batch.benchmark}_{batch.query_start}_{batch.query_end}_{batch.batch_id}"
    worker_container_name = f"worker_{batch.db_type}_{batch.benchmark}_{batch.query_start}_{batch.query_end}_{batch.batch_id}"

    # 배치별 CSV/로그 파일 경로 (호스트에서는 ./results 에서 확인)
    # Scheduler가 batch.result_csv를 "results/batch_{batch_id}.csv"로 지정했지만
    # 여기서는 명시적으로 파일명 구성 가능
    result_csv_path = f"/mnt/results/batch_{batch.batch_id}.csv"
    result_log_path = f"/mnt/results/batch_{batch.batch_id}.log"

    compose_content = f"""
version: '3.7'
services:
  {worker_container_name}:
    image: hoeunlee228/worker:latest
    container_name: {worker_container_name}
    environment:
      - DB_TYPE={batch.db_type}
      - DB_HOST={db_container_name}
      - DB_PORT={container_port}
      - DB_NAME=tpch
      - DB_USER={db_user}
      - DB_PASS={db_pass}
      - BENCHMARK={batch.benchmark}
      - QUERY_START={batch.query_start}
      - QUERY_END={batch.query_end}
      - REPEAT_COUNT={batch.repeat_count}
      - RESULT_CSV={result_csv_path}
      - RESULT_LOG={result_log_path}
    volumes:
      - ./results:/mnt/results
    depends_on:
      - {db_container_name}

  {db_container_name}:
    image: {db_image}
    container_name: {db_container_name}
    environment:
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_HOST_AUTH_METHOD=trust
      - ACCEPT_EULA=Y
      - MSSQL_SA_PASSWORD=Dlghdms0228
    """
    with open(batch.compose_file, 'w', encoding='utf-8') as f:
        f.write(compose_content)

def launch_batch(batch: Batch):
    generate_compose_file(batch)
    # docker compose 명령어 사용 (Compose v2)
    cmd = ["docker", "compose", "-f", batch.compose_file, "up", "-d"]
    print(f"Launching {batch}")
    try:
        subprocess.check_call(cmd)
        batch.status = "running"
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to launch batch {batch.batch_id}: {e}")

def stop_batch(batch: Batch):
    cmd = ["docker", "compose", "-f", batch.compose_file, "down"]
    print(f"Stopping batch {batch.batch_id} ...")
    try:
        subprocess.check_call(cmd)
        batch.status = "finished"
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to stop batch {batch.batch_id}: {e}")

def check_batch_finished(batch: Batch):
    if os.path.exists(batch.result_csv) and os.path.getsize(batch.result_csv) > 0:
        return True
    return False

def print_status(running, queue):
    print("\n=== Scheduler Status ===")
    if running:
        print("Running Batches:")
        for b in running:
            print(f"  {b}")
    else:
        print("No running batches.")
    print("Queue (top 5):")
    for i, b in enumerate(list(queue)[:5], start=1):
        print(f"  {i}. {b}")
    print(f"Running + queued: {len(running) + len(queue)}")
    print("========================\n")

def monitor_batches(running, queue, max_parallel, poll_interval=10):
    while running or queue:
        print_status(running, queue)

        # 1) 종료할 배치 체크
        for b in list(running):
            if check_batch_finished(b):
                print(f"[Batch {b.batch_id}] completed. Shutting down.")
                stop_batch(b)
                running.remove(b)

        # 2) 새 배치 시작
        while len(running) < max_parallel and queue:
            new_batch = queue.popleft()
            launch_batch(new_batch)
            running.append(new_batch)

        time.sleep(poll_interval)

def load_config(config_file):
    """
    config.yml 파일을 로드하여 dict 형태로 반환
    """
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config

def build_batch_queue(config):
    """
    config.yml 내용에 따라 배치 큐(deque)를 구성
    """
    batch_size    = config.get('batch_size', 10)
    repeat_count  = config.get('repeat_count', 10)
    benchmarks    = config.get('benchmarks', [])
    dbms_list     = config.get('dbms_list', [])

    batch_queue = deque()
    batch_id = 1

    for bm in benchmarks:
        bm_name = bm.get('name', 'tpch')
        total_q = bm.get('total_queries', 10)

        for db in dbms_list:
            db_name = db.get('name', 'postgres')
            start = 1
            while start <= total_q:
                end = min(start + batch_size - 1, total_q)
                batch_queue.append(
                    Batch(
                        batch_id=batch_id,
                        benchmark=bm_name,
                        query_start=start,
                        query_end=end,
                        db_type=db_name,
                        repeat_count=repeat_count
                    )
                )
                batch_id += 1
                start = end + 1

    return batch_queue

def main():
    parser = argparse.ArgumentParser(description="SQL Benchmark Scheduler")
    parser.add_argument("--config", default="config.yml", help="Path to configuration YAML file")
    args = parser.parse_args()

    # 1) config.yml 로드
    config = load_config(args.config)

    # 2) 배치 큐 생성
    batch_queue = build_batch_queue(config)
    running_batches = []

    # 3) 결과 디렉터리 준비
    os.makedirs("results", exist_ok=True)

    # 4) 스케줄링 시작
    max_parallel = config.get('max_parallel', 7)
    print("Scheduler starting...")
    monitor_batches(running_batches, batch_queue, max_parallel=max_parallel, poll_interval=10)
    print("All batches completed!")

if __name__ == "__main__":
    main()