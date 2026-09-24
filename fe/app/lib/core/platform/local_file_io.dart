import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/widgets.dart';

ImageProvider<Object> localImageProvider(String path) => FileImage(File(path));

bool localFileExists(String path) => File(path).existsSync();

Future<Uint8List> readLocalFile(String path) => File(path).readAsBytes();
