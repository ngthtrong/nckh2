import 'dart:io';

import 'package:app/data/datasources/user_local_datasource.dart';
import 'package:app/domain/entities/user.dart';
import 'package:app/domain/repositories/inference_repository.dart';
import 'package:app/domain/repositories/network_repository.dart';
import 'package:app/domain/repositories/rescue_repository.dart';
import 'package:app/presentation/controllers/app_controller.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive_ce_flutter/hive_flutter.dart';

class _Rescue implements RescueRepository {
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class _Inference implements InferenceRepository {
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class _Network implements NetworkRepository {
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late Directory dir;
  late UserLocalDataSource users;
  const user = User(
    username: 'rescue',
    password: 'password',
    phone: '123',
    address: 'Home',
  );

  setUp(() async {
    dir = await Directory.systemTemp.createTemp('user_session_test');
    Hive.init(dir.path);
    users = UserLocalDataSource();
    await users.init();
  });

  tearDown(() async {
    await Hive.deleteFromDisk();
    await dir.delete(recursive: true);
  });

  test('logout preserves the locally registered account', () async {
    final saved = await users.saveUser(user);
    await users.clearSession();
    expect(users.getUser()?.toJson(), saved.toJson());
    expect(users.isSignedIn, isFalse);
    await Hive.close();
    await users.init();
    expect(users.getUser()?.toJson(), saved.toJson());
    expect(users.isSignedIn, isFalse);
    await users.saveUser(users.getUser()!);
    expect(users.isSignedIn, isTrue);
  });

  test('existing current_user migrates to signed in once', () async {
    final box = Hive.box<Map>(UserLocalDataSource.boxName);
    const legacyPassword = 'legacy-password-secret-to-remove';
    await box.put(UserLocalDataSource.userKey, {
      ...user.toJson(),
      'password': legacyPassword,
    });
    await box.delete(UserLocalDataSource.sessionKey);
    await users.init();
    expect(users.isSignedIn, isTrue);
    expect(box.get(UserLocalDataSource.userKey), isNot(contains('password')));
    expect(users.getUser()?.password, isEmpty);
    expect(await users.authenticate(user.username, legacyPassword), isNotNull);
    await box.flush();
    final bytes = await File(box.path!).readAsBytes();
    expect(String.fromCharCodes(bytes), isNot(contains(legacyPassword)));
    await users.clearSession();
    await users.init();
    expect(users.isSignedIn, isFalse);
  });

  test(
    'password is salted, never serialized, and profile edits preserve hash',
    () async {
      expect(user.toJson(), isNot(contains('password')));
      final saved = await users.saveUser(user);
      expect(saved.password, isEmpty);
      expect(saved.passwordHash, startsWith(r'pbkdf2_sha256$200000$'));
      final box = Hive.box<Map>(UserLocalDataSource.boxName);
      expect(box.get(UserLocalDataSource.userKey), isNot(contains('password')));
      final edited = await users.saveUser(saved.copyWith(address: 'New home'));
      expect(edited.passwordHash, saved.passwordHash);
      expect(await users.authenticate(user.username, 'wrong'), isNull);
      expect(await users.authenticate(user.username, user.password), isNotNull);
      final second = await users.saveUser(user);
      expect(second.passwordHash, isNot(saved.passwordHash));
    },
  );

  test('PBKDF2 verifies the backend/Python SHA256 reference vector', () async {
    const hash =
        r'pbkdf2_sha256$200000$000102030405060708090a0b0c0d0e0f$581fe8327ebf9c191ed43b9aec17f821762c0a24aa35a933c8dc649cdc60feee';
    final box = Hive.box<Map>(UserLocalDataSource.boxName);
    await box.put(
      UserLocalDataSource.userKey,
      user.copyWith(password: '', passwordHash: hash).toJson(),
    );
    expect(await users.authenticate('rescue', 'password'), isNotNull);
    expect(await users.authenticate('rescue', 'incorrect'), isNull);
    await box.put(UserLocalDataSource.userKey, {
      ...user.toJson(),
      'passwordHash': r'pbkdf2_sha256$99999999999$00$00',
    });
    expect(await users.authenticate('rescue', 'password'), isNull);
  });

  test(
    'change password checks the old password and removes old access',
    () async {
      await users.saveUser(user);
      expect(await users.changePassword('wrong', 'new-password'), isNull);
      expect(await users.changePassword('password', 'tiny'), isNull);
      final updated = await users.changePassword('password', 'new-password');
      expect(updated?.password, isEmpty);
      expect(await users.authenticate('rescue', 'password'), isNull);
      expect(await users.authenticate('rescue', 'new-password'), isNotNull);
    },
  );

  test('demo credentials cannot overwrite a registered profile', () async {
    final saved = await users.saveUser(user);
    final controller = AppController(
      rescueRepository: _Rescue(),
      inferenceRepository: _Inference(),
      networkRepository: _Network(),
      userLocalDataSource: users,
    );
    addTearDown(controller.dispose);
    expect(await controller.login('cuuho', '123456'), isFalse);
    expect(users.getUser()?.toJson(), saved.toJson());
    expect(await controller.login('rescue', 'password'), isTrue);
    expect(controller.currentUser?.password, isEmpty);
    expect(await controller.changePassword('password', 'new-password'), isTrue);
    expect(await controller.login('rescue', 'new-password'), isTrue);
  });

  test(
    'logging out while password verification runs keeps the session closed',
    () async {
      await users.saveUser(user);
      final pending = users.authenticate('rescue', 'password');
      await users.clearSession();
      expect(await pending, isNull);
      expect(users.isSignedIn, isFalse);
    },
  );
}
