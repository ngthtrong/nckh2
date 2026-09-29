/// Thứ tự trạng thái cứu hộ; chỉ được đi tiến (contact_connect.md).
const rescueStatusOrder = ['processing', 'dispatched', 'resolved'];

/// Điều phối viên đóng báo cáo (trùng, báo giả, đã tự thoát...). Có thể đến từ
/// `processing` hoặc `dispatched`; cùng với `resolved` là trạng thái kết thúc.
const rescueStatusCancelled = 'cancelled';

/// Trạng thái kết thúc: app ngừng hỏi server về báo cáo này.
bool isFinalStatus(String status) =>
    status == rescueStatusOrder.last || status == rescueStatusCancelled;

/// Trạng thái mới nếu [server] tiến xa hơn [local], ngược lại null.
/// Trạng thái lạ hoặc lùi bị bỏ qua để app không hiển thị sai.
String? advancedStatus(String local, String? server) {
  if (server == null || isFinalStatus(local)) return null;
  if (server == rescueStatusCancelled) return server;
  final to = rescueStatusOrder.indexOf(server);
  if (to < 0) return null;
  return to > rescueStatusOrder.indexOf(local) ? server : null;
}
