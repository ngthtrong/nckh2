import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../controllers/app_controller.dart';

String adminLoginErrorMessage(Object exception) {
  if (exception is StateError) return exception.message.toString();
  if (exception is! DioException) return 'Đăng nhập quản trị thất bại.';

  final status = exception.response?.statusCode;
  if (status != null) {
    final detail = exception.response?.data is Map
        ? (exception.response!.data as Map)['detail']
        : null;
    final message = detail is Map ? detail['error'] : detail;
    if (message is String && message.isNotEmpty) {
      return 'Server trả HTTP $status: $message';
    }
    if (status >= 200 && status < 300) {
      return 'Server trả HTTP $status nhưng app không đọc được phản hồi đăng nhập.';
    }
    return 'Server trả lỗi HTTP $status.';
  }

  return switch (exception.type) {
    DioExceptionType.connectionTimeout => 'Hết thời gian kết nối đến server.',
    DioExceptionType.sendTimeout => 'Hết thời gian gửi yêu cầu đăng nhập.',
    DioExceptionType.receiveTimeout =>
      'Server không trả phản hồi đăng nhập kịp thời.',
    DioExceptionType.transformTimeout =>
      'Quá thời gian xử lý phản hồi đăng nhập.',
    DioExceptionType.connectionError => 'Không kết nối được server.',
    DioExceptionType.badCertificate => 'Chứng chỉ server không được tin cậy.',
    DioExceptionType.cancel => 'Yêu cầu đăng nhập đã bị hủy.',
    DioExceptionType.badResponse => 'Server trả phản hồi không hợp lệ.',
    DioExceptionType.unknown =>
      'Lỗi kết nối khi đăng nhập: '
      '${exception.message ?? exception.error ?? 'không rõ nguyên nhân'}',
  };
}

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
                error = adminLoginErrorMessage(exception);
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
