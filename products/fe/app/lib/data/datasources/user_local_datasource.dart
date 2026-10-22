import 'dart:math';

import 'package:cryptography/cryptography.dart';
import 'package:flutter/foundation.dart';
import 'package:hive_ce_flutter/hive_flutter.dart';
import '../../domain/entities/user.dart';

class UserLocalDataSource {
  static const String boxName = 'user_profile';
  static const String userKey = 'current_user';
  static const String sessionKey = '_session';
  Box<Map>? _box;
  int _revision = 0;

  Future<void> init() async {
    _box = await Hive.openBox<Map>(boxName);
    if (!_box!.containsKey(sessionKey)) {
      await _box!.put(sessionKey, {'signedIn': _box!.containsKey(userKey)});
    }
    final user = getUser();
    if (user != null && user.password.isNotEmpty) {
      await _box!.put(userKey, (await _protect(user)).toJson());
      // Hive appends writes; compact so the replaced plaintext leaves this file.
      await _box!.compact();
    }
  }

  bool get isSignedIn => _box?.get(sessionKey)?['signedIn'] == true;

  User? getUser() {
    final raw = _box?.get(userKey);
    if (raw == null) return null;
    return User.fromJson(Map<String, dynamic>.from(raw));
  }

  Future<User> saveUser(User user) async {
    final revision = _revision;
    final protected = await _protect(user);
    if (revision != _revision) throw StateError('Phiên đăng nhập đã thay đổi.');
    _revision++;
    await _box!.putAll({
      userKey: protected.toJson(),
      sessionKey: {'signedIn': true},
    });
    return protected;
  }

  Future<User> _protect(User user) async {
    final hash = user.password.isNotEmpty
        ? await compute(_hashPassword, user.password)
        : user.passwordHash;
    if (hash == null || hash.isEmpty) {
      throw StateError('Tài khoản chưa có mật khẩu.');
    }
    return User(
      username: user.username,
      phone: user.phone,
      address: user.address,
      passwordHash: hash,
    );
  }

  Future<User?> authenticate(String username, String password) async {
    final revision = _revision;
    final user = getUser();
    if (user == null || user.username != username.trim()) return null;
    final hash = user.passwordHash;
    if (hash == null || !await compute(_verifyPassword, (password, hash))) {
      return null;
    }
    if (revision != _revision) return null;
    return saveUser(user);
  }

  Future<User?> changePassword(String current, String next) async {
    final revision = _revision;
    if (next.length < 6) return null;
    final user = getUser();
    final hash = user?.passwordHash;
    if (user == null ||
        hash == null ||
        !await compute(_verifyPassword, (current, hash))) {
      return null;
    }
    if (revision != _revision) return null;
    return saveUser(user.copyWith(password: next));
  }

  Future<void> clearSession() async {
    _revision++;
    await _box?.put(sessionKey, {'signedIn': false});
  }
}

const _passwordIterations = 200000;

Future<String> _hashPassword(String password) async {
  final random = Random.secure();
  final salt = List<int>.generate(16, (_) => random.nextInt(256));
  final key = await Pbkdf2.hmacSha256(
    iterations: _passwordIterations,
    bits: 256,
  ).deriveKeyFromPassword(password: password, nonce: salt);
  return 'pbkdf2_sha256\$$_passwordIterations\$${_hex(salt)}\$${_hex(await key.extractBytes())}';
}

Future<bool> _verifyPassword((String, String) input) async {
  try {
    final parts = input.$2.split(r'$');
    if (parts.length != 4 || parts[0] != 'pbkdf2_sha256') return false;
    final iterations = int.parse(parts[1]);
    if (iterations < 1000 || iterations > 1000000) return false;
    final salt = _unhex(parts[2]);
    final expected = _unhex(parts[3]);
    if (salt.length != 16 || expected.length != 32) return false;
    final key = await Pbkdf2.hmacSha256(
      iterations: iterations,
      bits: 256,
    ).deriveKeyFromPassword(password: input.$1, nonce: salt);
    final actual = await key.extractBytes();
    var mismatch = 0;
    for (var i = 0; i < expected.length; i++) {
      mismatch |= expected[i] ^ actual[i];
    }
    return mismatch == 0;
  } on FormatException {
    return false;
  }
}

String _hex(List<int> bytes) =>
    bytes.map((byte) => byte.toRadixString(16).padLeft(2, '0')).join();

List<int> _unhex(String value) {
  if (value.length.isOdd || !RegExp(r'^[0-9a-fA-F]+$').hasMatch(value)) {
    throw const FormatException('Invalid hash bytes');
  }
  return [
    for (var i = 0; i < value.length; i += 2)
      int.parse(value.substring(i, i + 2), radix: 16),
  ];
}
