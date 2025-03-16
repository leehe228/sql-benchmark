#!/usr/bin/env python3
# sql-benchmark/scheduler.py

import os
import time
import subprocess
import yaml  # pip install pyyaml
from collections import deque

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
    배치별 docker-compose.yml 파일을 동적으로 생성.
    실제 환경에서는 템플릿 파일을 활용하거나 DB 접속 정보를 더 세부적으로 반영할 수 있음.
    """
    db_image_map = {
        "postgres": "postgres-tpch:latest",
        "mssql":    "mssql-tpch:latest"
    }
    db_image = db_image_map.get(batch.db_type.lower(), "postgres-tpch:latest")

    # 포트 매핑
    if batch.db_type.lower() == "mssql":
        port_mapping = "1433:1433"
        db_port = "1433"
        db_user = "SA"
        db_pass = "Dlghdms0228"
    else:
        port_mapping = "5432:5432"
        db_port = "5432"
        db_user = "postgres"
        db_pass = "postgres"

    compose_content = f"""
version: '3.7'
services:
  worker_{batch.batch_id}:
    image: worker-container:latest
    container_name: worker_{batch.batch_id}
    environment:
      - DB_TYPE={batch.db_type}
      - DB_HOST=db_{batch.batch_id}
      - DB_PORT={db_port}
      - DB_NAME=tpch
      - DB_USER={db_user}
      - DB_PASS={db_pass}
      - BENCHMARK={batch.benchmark}
      - QUERY_START={batch.query_start}
      - QUERY_END={batch.query_end}
      - REPEAT_COUNT={batch.repeat_count}
    volumes:
      - ./results:/mnt/results
    depends_on:
      - db_{batch.batch_id}

  db_{batch.batch_id}:
    image: {db_image}
    container_name: db_{batch.batch_id}
    ports:
      - "{port_mapping}"
    environment:
      - POSTGRES_PASSWORD=postgres
      - ACCEPT_EULA=Y
      - MSSQL_SA_PASSWORD=Dlghdms0228
    """

    with open(batch.compose_file, 'w', encoding='utf-8') as f:
        f.write(compose_content)

def launch_batch(batch: Batch):
    generate_compose_file(batch)
    cmd = ["docker-compose", "-f", batch.compose_file, "up", "-d"]
    print(f"Launching {batch}")
    try:
        subprocess.check_call(cmd)
        batch.status = "running"
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to launch {batch.batch_id}: {e}")

def stop_batch(batch: Batch):
    cmd = ["docker-compose", "-f", batch.compose_file, "down"]
    print(f"Stopping batch {batch.batch_id} ...")
    try:
        subprocess.check_call(cmd)
        batch.status = "finished"
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to stop {batch.batch_id}: {e}")

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

def load_config(config_file="config.yml"):
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
    repeat_count  = config.get('repeat_count', 5)
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
    # 1) config.yml 로드
    config = load_config("config.yml")

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