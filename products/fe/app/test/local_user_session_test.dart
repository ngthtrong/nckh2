import 'dart:io';

import 'package:app/data/datasources/user_local_datasource.dart';
import 'package:app/domain/entities/user.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive_ce_flutter/hive_flutter.dart';

void main() {
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
    await users.saveUser(user);
    await users.clearSession();
    expect(users.getUser()?.toJson(), user.toJson());
    expect(users.isSignedIn, isFalse);
    await Hive.close();
    await users.init();
    expect(users.getUser()?.toJson(), user.toJson());
    expect(users.isSignedIn, isFalse);
    await users.saveUser(users.getUser()!);
    expect(users.isSignedIn, isTrue);
  });

  test('existing current_user migrates to signed in once', () async {
    final box = Hive.box<Map>(UserLocalDataSource.boxName);
    await box.put(UserLocalDataSource.userKey, user.toJson());
    await box.delete(UserLocalDataSource.sessionKey);
    await users.init();
    expect(users.isSignedIn, isTrue);
    await users.clearSession();
    await users.init();
    expect(users.isSignedIn, isFalse);
  });
}
