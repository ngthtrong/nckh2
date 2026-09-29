/// Không cho app đang mở và tác vụ Workmanager (isolate khác, Hive riêng) cùng ghi
/// outbox: hai bên cấp trùng `sequence_number` (server trả `SEQUENCE_REUSED`) và
/// ghi đè bản ghi của nhau. Web không có Workmanager nên dùng bản rỗng.
library;

export 'sync_isolate_guard_stub.dart'
    if (dart.library.io) 'sync_isolate_guard_io.dart';
