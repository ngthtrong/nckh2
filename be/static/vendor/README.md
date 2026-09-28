# Thư viện bên thứ ba (đóng gói sẵn để dashboard chạy không cần CDN)

| Thư mục/tệp | Phiên bản | Giấy phép | Nguồn |
|---|---|---|---|
| `leaflet/` | Leaflet 1.9.4 | BSD-2-Clause (`leaflet/LICENSE`) | https://leafletjs.com |
| `leaflet-heat.js` | Leaflet.heat 0.2.0 (kèm simpleheat) | BSD-2-Clause (ghi trong đầu tệp) | https://github.com/Leaflet/Leaflet.heat |

Tải lại từ cdnjs khi cần nâng cấp; không sửa tay các tệp này. Tile bản đồ vẫn lấy
từ OpenStreetMap trừ khi đặt `RESCUE_TILE_URL` tới tile server nội bộ.
