import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:app/data/datasources/record_local_datasource.dart';
import 'package:app/data/datasources/sender_remote_datasource.dart';
import 'package:app/data/repositories/rescue_repository_impl.dart';
import 'package:app/domain/entities/rescue_image.dart';
import 'package:app/domain/entities/rescue_record.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive_ce/hive.dart';

class RecordingAdapter implements HttpClientAdapter {
  RecordingAdapter({this.failUpload = false});

  final bool failUpload;
  FormData? uploadedForm;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    if (options.path == '/probe') {
      return ResponseBody.fromBytes(Uint8List(300 * 1024), 200);
    }
    if (options.path == '/api/reports') {
      uploadedForm = options.data as FormData;
      if (failUpload) {
        return ResponseBody.fromString(
          jsonEncode({'detail': 'unavailable'}),
          503,
          headers: {
            Headers.contentTypeHeader: [Headers.jsonContentType],
          },
        );
      }
      final id = Map.fromEntries(uploadedForm!.fields)['report_id'];
      return ResponseBody.fromString(
        jsonEncode({'id': id}),
        201,
        headers: {
          Headers.contentTypeHeader: [Headers.jsonContentType],
        },
      );
    }
    return ResponseBody.fromString('', 404);
  }

  @override
  void close({bool force = false}) {}
}

RescueRecord sampleRecord() => RescueRecord(
  id: 'report-api',
  createdAt: DateTime.utc(2026, 9, 22, 4, 30),
  lat: 10.1234,
  lng: 106.5678,
  image: RescueImage(
    bytes: Uint8List.fromList([10, 20, 30]),
    fileName: 'scene.jpg',
    mimeType: 'image/jpeg',
  ),
  aiLabel: 'high',
  aiConfidence: 0.91,
  trappedCount: 2,
  injuredCount: 1,
  vulnerableGroups: const ['trẻ em', 'người cao tuổi'],
  description: 'Nước đang dâng',
  sendMode: 'direct',
);

Dio testDio(RecordingAdapter adapter) {
  final dio = Dio(BaseOptions(baseUrl: 'http://localhost'));
  dio.httpClientAdapter = adapter;
  return dio;
}

void main() {
  test('selects the upload image mode from measured throughput', () {
    expect(
      selectUploadImageMode(bytesPerSecond: 300 * 1024, hasImage: true),
      UploadImageMode.original,
    );
    expect(
      selectUploadImageMode(bytesPerSecond: 64 * 1024, hasImage: true),
      UploadImageMode.compressed,
    );
    expect(
      selectUploadImageMode(bytesPerSecond: 10 * 1024, hasImage: true),
      UploadImageMode.textOnly,
    );
    expect(
      selectUploadImageMode(bytesPerSecond: 1024 * 1024, hasImage: false),
      UploadImageMode.textOnly,
    );
  });

  test(
    'upload uses the FastAPI multipart contract with the real image',
    () async {
      final adapter = RecordingAdapter();
      final sender = SenderRemoteDataSource(dio: testDio(adapter));
      final record = sampleRecord();

      final result = await sender.upload(record, record.image?.bytes);
      final form = adapter.uploadedForm!;
      final fields = Map.fromEntries(form.fields);

      expect(result.ok, isTrue);
      expect(fields['report_id'], 'report-api');
      expect(fields['created_at'], '2026-09-22T04:30:00.000Z');
      expect(fields['trapped_count'], '2');
      expect(fields['injured_count'], '1');
      expect(fields['latitude'], '10.1234');
      expect(fields['longitude'], '106.5678');
      expect(jsonDecode(fields['vulnerable_groups']!), [
        'trẻ em',
        'người cao tuổi',
      ]);
      expect(form.files.single.key, 'image');
      expect(form.files.single.value.filename, 'scene.jpg');
      expect(form.files.single.value.length, 3);
    },
  );

  test('failed upload remains pending with a readable error', () async {
    final temporaryDirectory = await Directory.systemTemp.createTemp(
      'rescue-upload-test-',
    );
    Hive.init(temporaryDirectory.path);
    final box = await Hive.openBox<Map>('upload-records-test');
    final local = RecordLocalDataSource.withBox(box);
    final sender = SenderRemoteDataSource(
      dio: testDio(RecordingAdapter(failUpload: true)),
    );
    final repository = RescueRepositoryImpl(
      localDataSource: local,
      senderDataSource: sender,
    );
    final record = sampleRecord();

    await repository.saveRecord(record);
    final sent = await repository.sendRecord(record);
    final stored = repository.getAllRecords().single;

    expect(sent, isFalse);
    expect(stored.synced, isFalse);
    expect(stored.status, 'pending');
    expect(stored.lastError, isNotEmpty);

    await box.close();
    await Hive.close();
    await temporaryDirectory.delete(recursive: true);
  });
}
