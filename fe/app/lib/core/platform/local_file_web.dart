import 'dart:typed_data';

import 'package:cross_file/cross_file.dart';
import 'package:flutter/widgets.dart';

ImageProvider<Object> localImageProvider(String path) => NetworkImage(path);

bool localFileExists(String path) => path.isNotEmpty;

Future<Uint8List> readLocalFile(String path) => XFile(path).readAsBytes();
