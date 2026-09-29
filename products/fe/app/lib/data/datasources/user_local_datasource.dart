import 'package:hive_ce_flutter/hive_flutter.dart';
import '../../domain/entities/user.dart';

class UserLocalDataSource {
  static const String boxName = 'user_profile';
  static const String userKey = 'current_user';
  Box<Map>? _box;

  Future<void> init() async {
    _box = await Hive.openBox<Map>(boxName);
  }

  User? getUser() {
    final raw = _box?.get(userKey);
    if (raw == null) return null;
    return User.fromJson(Map<String, dynamic>.from(raw));
  }

  Future<void> saveUser(User user) async {
    await _box?.put(userKey, user.toJson());
  }

  Future<void> deleteUser() async {
    await _box?.delete(userKey);
  }
}
