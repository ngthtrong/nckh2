import 'package:hive_ce_flutter/hive_flutter.dart';
import '../../domain/entities/user.dart';

class UserLocalDataSource {
  static const String boxName = 'user_profile';
  static const String userKey = 'current_user';
  static const String sessionKey = '_session';
  Box<Map>? _box;

  Future<void> init() async {
    _box = await Hive.openBox<Map>(boxName);
    if (!_box!.containsKey(sessionKey)) {
      await _box!.put(sessionKey, {'signedIn': _box!.containsKey(userKey)});
    }
  }

  bool get isSignedIn => _box?.get(sessionKey)?['signedIn'] == true;

  User? getUser() {
    final raw = _box?.get(userKey);
    if (raw == null) return null;
    return User.fromJson(Map<String, dynamic>.from(raw));
  }

  Future<void> saveUser(User user) async {
    await _box?.putAll({
      userKey: user.toJson(),
      sessionKey: {'signedIn': true},
    });
  }

  Future<void> clearSession() async {
    await _box?.put(sessionKey, {'signedIn': false});
  }
}
