// Chọn lưu gói/checkpoint bằng file trên thiết bị; bản web không cho chạy E2E Android.
export 'mobile_e2e_storage_io.dart'
    if (dart.library.html) 'mobile_e2e_storage_web.dart';
