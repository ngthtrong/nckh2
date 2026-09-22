import 'dart:typed_data';

class RescueImage {
  const RescueImage({
    required this.bytes,
    required this.fileName,
    required this.mimeType,
  });

  final Uint8List bytes;
  final String fileName;
  final String mimeType;

  Map<String, dynamic> toMap() => {
    'bytes': bytes,
    'fileName': fileName,
    'mimeType': mimeType,
  };

  factory RescueImage.fromMap(Map<dynamic, dynamic> map) {
    final rawBytes = map['bytes'];
    return RescueImage(
      bytes: rawBytes is Uint8List
          ? rawBytes
          : Uint8List.fromList(List<int>.from(rawBytes as List)),
      fileName: map['fileName'] as String,
      mimeType: map['mimeType'] as String,
    );
  }
}
