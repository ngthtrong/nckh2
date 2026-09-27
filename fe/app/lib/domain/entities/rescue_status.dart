/// Thứ tự trạng thái cứu hộ; chỉ được đi tiến (contact_connect.md).
const rescueStatusOrder = ['processing', 'dispatched', 'resolved'];

/// Trạng thái mới nếu [server] tiến xa hơn [local], ngược lại null.
/// Trạng thái lạ hoặc lùi bị bỏ qua để app không hiển thị sai.
String? advancedStatus(String local, String? server) {
  final to = rescueStatusOrder.indexOf(server ?? '');
  if (to < 0) return null;
  return to > rescueStatusOrder.indexOf(local) ? server : null;
}
