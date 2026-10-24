import 'package:hive_ce_flutter/hive_flutter.dart';

/// A form snapshot is separate from reports so workers never send it as an SOS.
class ComposeDraftLocalDataSource {
  Box<Map>? _box;

  Future<void> init() async {
    _box = await Hive.openBox<Map>('compose_draft');
  }

  Map<String, dynamic>? read() {
    final value = _box?.get('draft');
    return value == null ? null : Map<String, dynamic>.from(value);
  }

  Future<void> save(Map<String, dynamic> draft) async {
    await _box!.put('draft', draft);
    // Finish writing before Android launches a camera/gallery Activity.
    await _box!.flush();
  }

  Future<void> clear() async {
    await _box!.delete('draft');
    await _box!.flush();
  }
}
