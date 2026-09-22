import 'dart:async';
import 'dart:js_interop';

import 'package:web/web.dart' as web;

Stream<void> browserOnlineEvents() {
  late final StreamController<void> controller;
  JSFunction? listener;

  controller = StreamController<void>.broadcast(
    onListen: () {
      listener = ((web.Event event) {
        controller.add(null);
      }).toJS;
      web.window.addEventListener('online', listener);
    },
    onCancel: () {
      final callback = listener;
      if (callback != null) {
        web.window.removeEventListener('online', callback);
      }
      listener = null;
    },
  );
  return controller.stream;
}
