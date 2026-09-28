import '../../config.dart';
import '../entities/send_mode.dart';
import '../repositories/network_repository.dart';

/// Kết quả chọn chế độ gửi, kèm throughput đo được (null nếu không đo).
typedef SendDecision = ({SendMode mode, int? throughputKbps});

/// Gửi thích ứng: đo throughput thật tới server qua `GET /probe` (64 KB) ngay
/// trước khi gửi, rồi chọn chế độ bằng [chooseMode] với ngưỡng trong config.dart.
class AdaptiveSendPolicy {
  final NetworkRepository network;

  const AdaptiveSendPolicy(this.network);

  /// [confidence] là độ tin cậy cao nhất của AI on-device (0 nếu không có).
  /// Báo cáo không có ảnh không cần đo: có kết nối thì gửi text, không thì SMS.
  Future<SendDecision> decide({
    required bool hasImage,
    required double confidence,
  }) async {
    if (!await _hasConnection()) {
      return (mode: SendMode.smsFallback, throughputKbps: null);
    }
    if (!hasImage) return (mode: SendMode.textOnly, throughputKbps: null);

    final kbps = await network.probeThroughputKbps();
    final mode = chooseMode(
      hasData: kbps != null,
      confidence: confidence,
      throughputKbps: kbps ?? 0,
      strongKbps: kStrongKbps,
      minUsefulKbps: kMinUsefulKbps,
      highConfidence: kHighConfidence,
      preferTextWhenConfident: kPreferTextWhenConfident,
    );
    return (mode: mode, throughputKbps: kbps);
  }

  Future<bool> _hasConnection() async {
    try {
      return await network.getCurrentNetworkType() != 'none';
    } catch (_) {
      // connectivity_plus lỗi trên một số desktop (WSL không có NetworkManager):
      // không kết luận là mất mạng, để bước gửi thật quyết định.
      return true;
    }
  }
}
