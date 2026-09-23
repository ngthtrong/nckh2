import 'dart:convert';

import 'package:causalontology/jcs.dart';
import 'package:crypto/crypto.dart';

String computePayloadHash(Object? payload) =>
    'sha256:${sha256.convert(utf8.encode(jcs(payload)))}';
