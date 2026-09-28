import 'package:uuid/uuid.dart';

/// ID báo cáo: `<prefix>-<epoch ms>-<12 hex ngẫu nhiên>`.
///
/// Phần ngẫu nhiên để hai máy bấm cùng mili-giây không trùng ID (server gộp theo
/// ID) và để người ngoài không đoán được ID của báo cáo khác. Server chỉ coi ID là
/// chuỗi (`[A-Za-z0-9._:-]`, tối đa 128 ký tự) nên ID dạng cũ vẫn hợp lệ.
String newRecordId(String prefix) {
  final random = const Uuid().v4().replaceAll('-', '').substring(0, 12);
  return '$prefix-${DateTime.now().millisecondsSinceEpoch}-$random';
}
