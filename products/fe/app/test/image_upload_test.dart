import 'dart:typed_data';

import 'package:app/data/datasources/sender_remote_datasource.dart';
import 'package:flutter_test/flutter_test.dart';

UploadResult _result(int? status, {bool? permanent}) => (
  ok: status == 201,
  bytesSent: 0,
  durationMs: 0,
  status: status,
  permanent: permanent ?? isPermanentUploadFailure(status, null),
);

void main() {
  final jpeg = Uint8List.fromList([0xFF, 0xD8, 0xFF, 0xE0, 0, 0]);

  test('nhận diện định dạng ảnh như server', () {
    expect(isServerSupportedImage(jpeg), isTrue);
    expect(
      isServerSupportedImage(
        Uint8List.fromList([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 1]),
      ),
      isTrue,
    );
    expect(
      isServerSupportedImage(
        Uint8List.fromList('RIFF\x00\x00\x00\x00WEBPVP8 '.codeUnits),
      ),
      isTrue,
    );
    // HEIC: hộp ftyp ở byte 4.
    expect(
      isServerSupportedImage(
        Uint8List.fromList([0, 0, 0, 24, ...'ftypheic'.codeUnits]),
      ),
      isFalse,
    );
    expect(isServerSupportedImage(Uint8List(0)), isFalse);
  });

  test('phân loại lỗi upload', () {
    expect(isPermanentUploadFailure(null, null), isFalse); // mất mạng
    expect(isPermanentUploadFailure(503, null), isFalse);
    expect(isPermanentUploadFailure(408, null), isFalse);
    expect(isPermanentUploadFailure(429, null), isFalse);
    expect(
      isPermanentUploadFailure(400, {'detail': 'IMAGE_HASH_MISMATCH'}),
      isFalse,
    );
    // Server hiện tại trả {code, error}; ảnh hỏng trên đường truyền vẫn gửi lại.
    expect(
      isPermanentUploadFailure(400, {
        'detail': {'code': 'IMAGE_HASH_MISMATCH', 'error': '...'},
      }),
      isFalse,
    );
    expect(
      isPermanentUploadFailure(409, {
        'detail': {'code': 'REPORT_ID_CONFLICT'},
      }),
      isTrue,
    );
    expect(
      isPermanentUploadFailure(415, {
        'detail': {'code': 'UNSUPPORTED_IMAGE'},
      }),
      isTrue,
    );
    expect(
      isPermanentUploadFailure(400, {
        'detail': {'code': 'INVALID_PAYLOAD'},
      }),
      isTrue,
    );
    expect(isPermanentUploadFailure(413, null), isTrue);
  });

  group('deliverImage', () {
    Future<(bool, List<int>, int?)> run(
      List<UploadResult> responses, {
      bool allowShrink = true,
    }) async {
      final sizes = <int>[];
      int? gaveUp;
      var call = 0;
      final done = await deliverImage(
        Uint8List(100),
        upload: (bytes) async {
          sizes.add(bytes.length);
          return responses[call++];
        },
        shrink: (bytes) async => Uint8List(10),
        allowShrink: allowShrink,
        onGiveUp: (status) => gaveUp = status,
      );
      return (done, sizes, gaveUp);
    }

    test('thành công', () async {
      expect((await run([_result(201)])).$1, isTrue);
    });

    test('lỗi mạng / 5xx: thử lại lần đồng bộ sau', () async {
      expect((await run([_result(null)])).$1, isFalse);
      expect((await run([_result(502)])).$1, isFalse);
    });

    test('bị từ chối vĩnh viễn (415): bỏ ảnh, không kẹt', () async {
      final (done, sizes, gaveUp) = await run([_result(415)]);
      expect(done, true);
      expect(sizes, [100]);
      expect(gaveUp, 415);
    });

    test('413: nén rồi gửi lại một lần', () async {
      final (done, sizes, gaveUp) = await run([_result(413), _result(201)]);
      expect(done, true);
      expect(sizes, [100, 10]);
      expect(gaveUp, null);
    });

    test('413 khi ảnh đã nén: bỏ ảnh', () async {
      final (done, sizes, gaveUp) = await run([
        _result(413),
      ], allowShrink: false);
      expect(done, true);
      expect(sizes, [100]);
      expect(gaveUp, 413);
    });

    test('413 rồi mất mạng khi gửi bản nén: thử lại sau', () async {
      expect((await run([_result(413), _result(null)])).$1, isFalse);
    });
  });
}
