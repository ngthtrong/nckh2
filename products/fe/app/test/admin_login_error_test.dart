import 'package:app/presentation/widgets/admin_login_button.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('shows the server reason for an HTTP authentication failure', () {
    final request = RequestOptions(path: '/api/auth/login');
    final error = DioException(
      requestOptions: request,
      response: Response(
        requestOptions: request,
        statusCode: 401,
        data: {
          'detail': {'error': 'Sai tên đăng nhập hoặc mật khẩu'},
        },
      ),
    );

    expect(
      adminLoginErrorMessage(error),
      'Server trả HTTP 401: Sai tên đăng nhập hoặc mật khẩu',
    );
  });

  test('distinguishes a response timeout from rejected credentials', () {
    final error = DioException(
      requestOptions: RequestOptions(path: '/api/auth/login'),
      type: DioExceptionType.receiveTimeout,
    );

    expect(
      adminLoginErrorMessage(error),
      'Server không trả phản hồi đăng nhập kịp thời.',
    );
  });

  test('maps response transformation timeouts', () {
    final error = DioException(
      requestOptions: RequestOptions(path: '/api/auth/login'),
      type: DioExceptionType.transformTimeout,
    );

    expect(
      adminLoginErrorMessage(error),
      'Quá thời gian xử lý phản hồi đăng nhập.',
    );
  });

  test('preserves server-side role validation errors', () {
    expect(
      adminLoginErrorMessage(
        StateError('Tài khoản cần có quyền admin trên server.'),
      ),
      'Tài khoản cần có quyền admin trên server.',
    );
  });
}
