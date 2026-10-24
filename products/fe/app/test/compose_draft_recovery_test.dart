import 'dart:io';

import 'package:app/data/datasources/compose_draft_local_datasource.dart';
import 'package:app/domain/repositories/inference_repository.dart';
import 'package:app/domain/repositories/network_repository.dart';
import 'package:app/domain/repositories/rescue_repository.dart';
import 'package:app/domain/entities/rescue_record.dart';
import 'package:app/presentation/controllers/app_controller.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive_ce_flutter/hive_flutter.dart';
import 'package:image_picker/image_picker.dart';

class _Rescue extends Fake implements RescueRepository {
  final records = <RescueRecord>[];
  @override
  List<RescueRecord> getAllRecords() => records;
}

class _Inference extends Fake implements InferenceRepository {}

class _Network extends Fake implements NetworkRepository {}

class _FailingCopiedDrafts extends ComposeDraftLocalDataSource {
  int saves = 0;
  String? failedCopyPath;

  @override
  Future<void> save(Map<String, dynamic> draft) async {
    await super.save(draft);
    if (++saves == 2) {
      failedCopyPath = draft['imagePath'] as String;
      throw StateError('Snapshot flush failed after writing the copied path.');
    }
  }
}

class _Picker extends Fake implements ImagePicker {
  LostDataResponse lost = LostDataResponse.empty();
  XFile? selected;
  @override
  Future<LostDataResponse> retrieveLostData() async => lost;
  @override
  Future<XFile?> pickImage({
    required ImageSource source,
    double? maxWidth,
    double? maxHeight,
    int? imageQuality,
    CameraDevice preferredCameraDevice = CameraDevice.rear,
    bool requestFullMetadata = true,
  }) async => selected;
}

void main() {
  final binding = TestWidgetsFlutterBinding.ensureInitialized();
  const pathChannel = MethodChannel('plugins.flutter.io/path_provider');
  late Directory dir;
  late ComposeDraftLocalDataSource drafts;
  late _Picker picker;
  late _Rescue rescue;
  AppController controller() => AppController(
    rescueRepository: rescue,
    inferenceRepository: _Inference(),
    networkRepository: _Network(),
    composeDraftLocalDataSource: drafts,
    picker: picker,
  );

  setUp(() async {
    dir = await Directory.systemTemp.createTemp('compose_draft_test');
    Hive.init(dir.path);
    drafts = ComposeDraftLocalDataSource();
    await drafts.init();
    picker = _Picker();
    rescue = _Rescue();
    debugDefaultTargetPlatformOverride = TargetPlatform.android;
    binding.defaultBinaryMessenger.setMockMethodCallHandler(
      pathChannel,
      (_) async => '${dir.path}/documents',
    );
  });
  tearDown(() async {
    debugDefaultTargetPlatformOverride = null;
    binding.defaultBinaryMessenger.setMockMethodCallHandler(pathChannel, null);
    await Hive.close();
    await dir.delete(recursive: true);
  });

  test(
    'draft and recovered camera photo survive Hive restart and cache deletion',
    () async {
      final photo = File('${dir.path}/camera.jpg');
      await photo.writeAsBytes([0xff, 0xd8, 0xff, 42]);
      await drafts.save({
        'description': 'Nước tới mái',
        'trappedCount': 3,
        'injuredCount': 1,
        'vulnerableGroups': ['Trẻ em'],
        'cannotMove': true,
        'severeSigns': ['heavy_bleeding'],
        'imagePath': null,
      });
      await Hive.close();
      drafts = ComposeDraftLocalDataSource();
      await drafts.init();
      picker.lost = LostDataResponse(files: [XFile(photo.path)]);
      final app = controller();
      addTearDown(app.dispose);
      await app.recoverPickerDraft();
      await photo.delete();
      final draft = app.composeDraft!;
      expect(draft['description'], 'Nước tới mái');
      expect(draft['trappedCount'], 3);
      expect(draft['cannotMove'], true);
      expect(draft['severeSigns'], ['heavy_bleeding']);
      expect(await File(draft['imagePath'] as String).readAsBytes(), [
        0xff,
        0xd8,
        0xff,
        42,
      ]);
      await Hive.close();
      await drafts.init();
      expect(drafts.read()!['imagePath'], draft['imagePath']);
      await app.clearComposeDraft();
      expect(app.composeDraft, isNull);
    },
  );

  test(
    'picker failure preserves draft and explains recovery failure',
    () async {
      await drafts.save({'description': 'Cần xuồng', 'trappedCount': 2});
      picker.lost = LostDataResponse(
        exception: PlatformException(code: 'camera-failed'),
      );
      final app = controller();
      addTearDown(app.dispose);
      await app.recoverPickerDraft();
      expect(app.composeDraft!['description'], 'Cần xuồng');
      expect(app.composeDraft!['recoveryError'], contains('chọn lại ảnh'));
    },
  );

  test(
    'ordinary picker result is copied out of temporary camera storage',
    () async {
      final photo = File('${dir.path}/camera.jpg');
      await photo.writeAsBytes([1, 2, 3]);
      picker.selected = XFile(photo.path);
      final app = controller();
      addTearDown(app.dispose);
      final saved = await app.pickImage(source: ImageSource.camera);
      await photo.delete();
      expect(await File(saved!).readAsBytes(), [1, 2, 3]);
    },
  );

  test('ordinary restart discards the picker snapshot', () async {
    await drafts.save({'description': 'Old camera snapshot'});
    await Hive.close();
    await drafts.init();
    final app = controller();
    addTearDown(app.dispose);
    await app.recoverPickerDraft();
    expect(app.composeDraft, isNull);
  });

  test(
    'successive images have distinct paths and retain their own bytes',
    () async {
      final photo = File('${dir.path}/camera.jpg');
      picker.selected = XFile(photo.path);
      final app = controller();
      addTearDown(app.dispose);
      await photo.writeAsBytes([1, 2, 3]);
      final first = await app.pickImage(source: ImageSource.camera);
      await photo.writeAsBytes([4, 5, 6]);
      final second = await app.pickImage(source: ImageSource.camera);
      expect(second, isNot(first));
      expect(await File(first!).readAsBytes(), [1, 2, 3]);
      expect(await File(second!).readAsBytes(), [4, 5, 6]);
    },
  );

  Future<File> composeFile(int id) async {
    final attachments = await Directory(
      '${dir.path}/documents/rescue_attachments',
    ).create(recursive: true);
    return File(
      '${attachments.path}/compose-image-$id-abcdef012345',
    ).writeAsBytes([id]);
  }

  test(
    'startup removes abandoned images and preserves report references',
    () async {
      final orphan = await composeFile(1);
      final primary = await composeFile(2);
      final additional = await composeFile(3);
      await drafts.save({'imagePath': orphan.path});
      rescue.records.add(
        RescueRecord(
          id: 'report',
          createdAt: DateTime(2026),
          lat: null,
          lng: null,
          sendMode: 'queuedOffline',
          imagePath: primary.path,
          images: [additional.path],
        ),
      );
      final app = controller();
      addTearDown(app.dispose);

      await app.recoverPickerDraft();

      expect(app.composeDraft, isNull);
      expect(await orphan.exists(), isFalse);
      expect(await primary.exists(), isTrue);
      expect(await additional.exists(), isTrue);
    },
  );

  test(
    'startup preserves recovered picker image and removes old compose copy',
    () async {
      final old = await composeFile(1);
      final photo = await File(
        '${dir.path}/camera.jpg',
      ).writeAsBytes([7, 8, 9]);
      await drafts.save({'description': 'Cần xuồng', 'imagePath': old.path});
      picker.lost = LostDataResponse(files: [XFile(photo.path)]);
      final app = controller();
      addTearDown(app.dispose);

      await app.recoverPickerDraft();

      final recoveredPath = app.composeDraft!['imagePath'] as String;
      expect(recoveredPath, isNot(old.path));
      expect(await File(recoveredPath).readAsBytes(), [7, 8, 9]);
      expect(await old.exists(), isFalse);
    },
  );

  test(
    'failed picker recovery preserves snapshot image during sweep',
    () async {
      final saved = await composeFile(1);
      final orphan = await composeFile(2);
      await drafts.save({'imagePath': saved.path});
      picker.lost = LostDataResponse(
        exception: PlatformException(code: 'camera-failed'),
      );
      final app = controller();
      addTearDown(app.dispose);

      await app.recoverPickerDraft();

      expect(app.composeDraft!['imagePath'], saved.path);
      expect(await saved.exists(), isTrue);
      expect(await orphan.exists(), isFalse);
    },
  );

  test(
    'discard keeps snapshot and report images until no longer referenced',
    () async {
      final snapshot = await composeFile(1);
      final primary = await composeFile(2);
      final additional = await composeFile(3);
      final orphan = await composeFile(4);
      await drafts.save({'imagePath': snapshot.path});
      rescue.records.add(
        RescueRecord(
          id: 'report',
          createdAt: DateTime(2026),
          lat: null,
          lng: null,
          sendMode: 'queuedOffline',
          imagePath: primary.path,
          images: [additional.path],
        ),
      );
      final app = controller();
      addTearDown(app.dispose);

      for (final file in [snapshot, primary, additional, orphan]) {
        await app.discardComposeImage(file.path);
      }
      await app.discardComposeImage(null);
      expect(await orphan.exists(), isFalse);
      expect(await snapshot.exists(), isTrue);
      expect(await primary.exists(), isTrue);
      expect(await additional.exists(), isTrue);

      await app.clearComposeDraft();
      expect(await snapshot.exists(), isTrue);
      await app.discardComposeImage(snapshot.path);
      expect(await snapshot.exists(), isFalse);
    },
  );

  test(
    'snapshot save failure reclaims only the newly copied picker photo',
    () async {
      final unrelated = await composeFile(1);
      final photo = await File(
        '${dir.path}/camera.jpg',
      ).writeAsBytes([7, 8, 9]);
      final failingDrafts = _FailingCopiedDrafts();
      await failingDrafts.init();
      drafts = failingDrafts;
      picker.selected = XFile(photo.path);
      final app = controller();
      addTearDown(app.dispose);

      await expectLater(
        app.pickImage(source: ImageSource.camera),
        throwsA(isA<FormatException>()),
      );

      expect(failingDrafts.failedCopyPath, isNotNull);
      expect(await File(failingDrafts.failedCopyPath!).exists(), isFalse);
      expect(app.composeDraft, isNull);
      expect(await photo.readAsBytes(), [7, 8, 9]);
      expect(await unrelated.exists(), isTrue);
    },
  );
}
