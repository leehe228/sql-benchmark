#!/bin/bash

# 작업 디렉토리 설정
WORK_DIR="./tpch-dbgen"

# tpch-dbgen 디렉토리로 이동
cd "$WORK_DIR" || exit 1

# 모든 .tbl 파일에 대해 마지막 | 제거
for file in *.tbl; do
    # 새로운 파일 이름 정의
    cleaned_file="${file%.tbl}_cleaned.tbl"
    
    # 마지막 | 제거하고 새 파일에 저장
    sed 's/|$//' "$file" > "$cleaned_file"
    
    # 완료 메시지 출력
    echo "Processed $file -> $cleaned_file"
done

echo "All files processed. '_cleaned.tbl' files created for each table."