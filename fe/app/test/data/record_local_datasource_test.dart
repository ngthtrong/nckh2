import 'dart:io';
import 'dart:typed_data';

import 'package:app/data/datasources/record_local_datasource.dart';
import 'package:app/domain/entities/rescue_image.dart';
import 'package:app/domain/entities/rescue_record.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive_ce/hive.dart';

void main() {
  late Directory temporaryDirectory;
  late Box<Map> box;
  late RecordLocalDataSource dataSource;

  setUp(() async {
    temporaryDirectory = await Directory.systemTemp.createTemp(
      'rescue-record-test-',
    );
    Hive.init(temporaryDirectory.path);
    box = await Hive.openBox<Map>('records-test');
    dataSource = RecordLocalDataSource.withBox(box);
  });

  tearDown(() async {
    await box.close();
    await Hive.close();
    await temporaryDirectory.delete(recursive: true);
  });

  test('record image bytes survive save and read', () async {
    final record = RescueRecord(
      id: 'report-storage',
      createdAt: DateTime.utc(2026, 9, 22, 4, 30),
      lat: 10.1234,
      lng: 106.5678,
      image: RescueImage(
        bytes: Uint8List.fromList([1, 2, 3, 4]),
        fileName: 'scene.png',
        mimeType: 'image/png',
      ),
      aiLabel: 'high',
      aiConfidence: 0.91,
      trappedCount: 2,
      injuredCount: 1,
      vulnerableGroups: const ['trẻ em'],
      description: 'Nước đang dâng',
      sendMode: 'direct',
      status: 'pending',
      lastError: 'Mất kết nối',
    );

    await dataSource.saveRecord(record);
    final restored = dataSource.getAllRecords().single;

    expect(restored.id, 'report-storage');
    expect(restored.image?.bytes, [1, 2, 3, 4]);
    expect(restored.image?.fileName, 'scene.png');
    expect(restored.image?.mimeType, 'image/png');
    expect(restored.aiLabel, 'high');
    expect(restored.aiConfidence, 0.91);
    expect(restored.trappedCount, 2);
    expect(restored.injuredCount, 1);
    expect(restored.vulnerableGroups, ['trẻ em']);
    expect(restored.description, 'Nước đang dâng');
    expect(restored.status, 'pending');
    expect(restored.lastError, 'Mất kết nối');
  });

  test('copyWith can clear a sync error after a successful upload', () {
    final failed = RescueRecord(
      id: 'report-retry',
      createdAt: DateTime.utc(2026, 9, 22),
      lat: 10,
      lng: 106,
      sendMode: 'textOnly',
      status: 'pending',
      lastError: 'Mất kết nối',
    );

    final synced = failed.copyWith(
      synced: true,
      status: 'dispatched',
      lastError: null,
    );

    expect(synced.synced, isTrue);
    expect(synced.status, 'dispatched');
    expect(synced.lastError, isNull);
  });
}
