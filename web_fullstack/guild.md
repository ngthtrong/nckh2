Chạy frontend
- cần có đường dẫn để khi gọi backend cũng sẽ ngay http này, nếu không có url flutter mặc định sẽ vào đường dẫn khác
cd fe/app
flutter run -d chrome --dart-define=API_BASE_URL=http://127.0.0.1:8000 


Chạy backend
.\web_fullstack\scripts\run_backend.ps1

Backend chạy tại http://127.0.0.1:8000

Swagger tại http://127.0.0.1:8000/docs

Xem tên tiến trình theo cổng 8000:
Get-NetTCPConnection -LocalPort 8000 -State Listen |
  ForEach-Object { Get-Process -Id $_.OwningProcess }


Dừng tiến trình ở cổng 8000:
Get-NetTCPConnection -LocalPort 8000 -State Listen |
  ForEach-Object { Stop-Process -Id $_.OwningProcess }
