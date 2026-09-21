import 'dart:async';
import 'dart:js_interop';

import 'package:web/web.dart' as web;

Stream<void> get browserOnlineEvents {
  late final web.EventListener listener;
  late final StreamController<void> controller;

  controller = StreamController<void>.broadcast(
    onListen: () {
      listener = ((web.Event _) => controller.add(null)).toJS;
      web.window.addEventListener('online', listener);
    },
    onCancel: () => web.window.removeEventListener('online', listener),
  );

  return controller.stream;
}
