import 'inference_data_source.dart';
import 'inference_native_data_source.dart'
    if (dart.library.js_interop) 'inference_web_data_source.dart'
    as platform;

InferenceDataSource createInferenceDataSource() =>
    platform.createInferenceDataSource();
