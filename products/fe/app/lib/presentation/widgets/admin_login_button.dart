import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../controllers/app_controller.dart';

class AdminLoginButton extends StatelessWidget {
  const AdminLoginButton({super.key, required this.controller, this.onSuccess});
  final AppController controller;
  final VoidCallback? onSuccess;

  Future<void> _login(BuildContext context) async {
    final username = TextEditingController();
    final password = TextEditingController();
    String? error;
    var busy = false;
    final accepted = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, update) {
          Future<void> submit() async {
            if (busy) return;
            if (username.text.trim().isEmpty || password.text.isEmpty) {
              update(
                () => error = 'Nhập tài khoản và mật khẩu admin trên server.',
              );
              return;
            }
            update(() {
              busy = true;
              error = null;
            });
            try {
              await controller.loginAdmin(username.text, password.text);
              if (dialogContext.mounted) Navigator.pop(dialogContext, true);
            } catch (exception) {
              if (!dialogContext.mounted) return;
              update(() {
                busy = false;
                error = exception is DioException
                    ? 'Không đăng nhập được. Kiểm tra server, tài khoản và mật khẩu.'
                    : 'Tài khoản cần có quyền admin trên server.';
              });
            }
          }

          return PopScope(
            canPop: !busy,
            child: AlertDialog(
              title: const Text('Đăng nhập quản trị'),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(controller.adminServerUrl),
                    const SizedBox(height: 12),
                    TextField(
                      controller: username,
                      enabled: !busy,
                      autocorrect: false,
                      decoration: const InputDecoration(
                        labelText: 'Tài khoản admin',
                      ),
                    ),
                    TextField(
                      controller: password,
                      enabled: !busy,
                      obscureText: true,
                      decoration: const InputDecoration(
                        labelText: 'Mật khẩu server',
                      ),
                      onSubmitted: (_) => submit(),
                    ),
                    if (error != null)
                      Text(error!, style: const TextStyle(color: Colors.red)),
                    if (busy) const LinearProgressIndicator(),
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: busy
                      ? null
                      : () => Navigator.pop(dialogContext, false),
                  child: const Text('Hủy'),
                ),
                FilledButton(
                  onPressed: busy ? null : submit,
                  child: const Text('Đăng nhập'),
                ),
              ],
            ),
          );
        },
      ),
    );
    // Let the route finish its closing animation before disposing field controllers.
    await Future<void>.delayed(const Duration(milliseconds: 300));
    username.dispose();
    password.dispose();
    if (accepted == true) onSuccess?.call();
  }

  @override
  Widget build(BuildContext context) => TextButton.icon(
    onPressed: () => _login(context),
    icon: const Icon(Icons.admin_panel_settings_outlined),
    label: const Text('Đăng nhập quản trị'),
  );
}
