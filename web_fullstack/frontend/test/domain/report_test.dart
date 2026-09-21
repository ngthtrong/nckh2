import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:flood_rescue_web/domain/report.dart';

void main() {
  test('report preserves image bytes and pending state', () {
    final report = RescueReport.draft(
      id: 'r1',
      imageBytes: Uint8List.fromList([1, 2, 3]),
      imageName: 'scene.jpg',
      imageMimeType: 'image/jpeg',
    );

    final restored = RescueReport.fromMap(report.toMap());

    expect(restored.id, 'r1');
    expect(restored.imageBytes, [1, 2, 3]);
    expect(restored.imageName, 'scene.jpg');
    expect(restored.imageMimeType, 'image/jpeg');
    expect(restored.syncState, SyncState.pending);
  });

  test('round trip preserves inference, location and rescue fields', () {
    final report = RescueReport(
      id: 'complete',
      createdAt: DateTime.utc(2026, 9, 21, 10),
      description: 'Nước ngập nhanh',
      trappedCount: 3,
      injuredCount: 1,
      vulnerableGroups: const ['trẻ em', 'người cao tuổi'],
      aiLabel: 'high',
      aiConfidence: 0.91,
      latitude: 10.762622,
      longitude: 106.660172,
      syncState: SyncState.synced,
    );

    final restored = RescueReport.fromMap(report.toMap());

    expect(restored.toMap(), report.toMap());
  });

  test('copyWith can clear sync error after a successful upload', () {
    final failed = RescueReport.draft(id: 'r2').copyWith(
      syncState: SyncState.pending,
      syncError: 'Không kết nối được',
    );

    final synced = failed.copyWith(
      syncState: SyncState.synced,
      clearSyncError: true,
    );

    expect(synced.syncState, SyncState.synced);
    expect(synced.syncError, isNull);
  });
}
