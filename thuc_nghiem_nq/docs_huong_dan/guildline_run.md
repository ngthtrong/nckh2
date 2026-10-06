1/ flutter: flutter run -d windows --dart-define=SERVER_URL=http://localhost:8000

backend: .\.venv\Scripts\Activate.ps1

`python -m pip install -r requirements.txt`

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

dashboard: http://localhost:8000/

2/ chạy bằng docker

`docker compose up -d --build`

docker compose ps

#Dừng dữ liệu

docker compose down

3/ kiểm tra database sql

SELECT
    id,
    server_received_at,
    created_at,
    description,
    status,
    send_mode,
    raw_payload
FROM reports
ORDER BY server_received_at DESC;


4/ kiểm tra db trong terminal bằng docker

docker compose exec be python -m sqlite3 /var/lib/rescue/rescue_reports.db

Khi xuất hiện dấu nhắc `sqlite>`, nhập:

	.headers on

	.mode column

Xem tổng số báo cáo hiện có:

	`SELECT COUNT(*) AS tong_bao_cao FROM reports;`

Xem toàn bộ báo cáo, mới nhất ở trên: 	

```
SELECT
    id,
    server_received_at,
    description,
    status,
    send_mode
FROM reports
ORDER BY server_received_at DESC;
```

Chỉ xem bài do app gửi, bỏ dữ liệu mô phỏng:

```
SELECT
    id,
    server_received_at,
    description,
    status,
    send_mode,
    raw_payload
FROM reports
WHERE id NOT LIKE 'sim-%'
ORDER BY server_received_at DESC;
```


Thoát bằng: .quit
