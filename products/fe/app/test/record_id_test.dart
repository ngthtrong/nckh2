import 'package:app/domain/entities/record_id.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('ID báo cáo khác nhau kể cả khi tạo cùng mili-giây và hợp lệ với server', () {
    final ids = List.generate(1000, (_) => newRecordId('sos'));
    expect(ids.toSet().length, ids.length);
    final pattern = RegExp(r'^sos-\d+-[0-9a-f]{12}$');
    expect(ids.every(pattern.hasMatch), isTrue);
  });
}
