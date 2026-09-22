Chạy frontend
- cần có đường dẫn để khi gọi backend cũng sẽ ngay http này, nếu không có url flutter mặc định sẽ vào đường dẫn khác
cd fe/app
flutter run -d chrome --dart-define=API_BASE_URL=http://127.0.0.1:8000 


