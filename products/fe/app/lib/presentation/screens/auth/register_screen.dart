import 'package:flutter/material.dart';

import '../../../../core/constants/app_colors.dart';
import '../../../domain/entities/user.dart';
import '../../controllers/app_controller.dart';

class RegisterScreen extends StatefulWidget {
  final AppController controller;
  final VoidCallback onGoLogin;
  final VoidCallback onRegisterSuccess;

  const RegisterScreen({
    super.key,
    required this.controller,
    required this.onGoLogin,
    required this.onRegisterSuccess,
  });

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  final _phoneController = TextEditingController();
  final _addressController = TextEditingController();

  bool _showPassword = false;
  bool _showConfirm = false;
  String? _errorMessage;
  bool _isLoading = false;

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _phoneController.dispose();
    _addressController.dispose();
    super.dispose();
  }

  bool _validate() {
    final username = _usernameController.text.trim();
    final password = _passwordController.text;
    final confirm = _confirmPasswordController.text;
    final phone = _phoneController.text.trim();
    final address = _addressController.text.trim();

    if (username.isEmpty || password.isEmpty || phone.isEmpty || address.isEmpty) {
      setState(() => _errorMessage = 'Vui lòng điền đầy đủ các mục.');
      return false;
    }
    if (username.length < 3) {
      setState(() => _errorMessage = 'Tên đăng nhập tối thiểu 3 ký tự.');
      return false;
    }
    if (password.length < 6) {
      setState(() => _errorMessage = 'Mật khẩu tối thiểu 6 ký tự.');
      return false;
    }
    if (password != confirm) {
      setState(() => _errorMessage = 'Mật khẩu xác nhận không khớp.');
      return false;
    }
    if (!RegExp(r'^[0-9]{9,11}$').hasMatch(phone.replaceAll(' ', ''))) {
      setState(() => _errorMessage = 'Số điện thoại không hợp lệ (9-11 chữ số).');
      return false;
    }
    return true;
  }

  Future<void> _handleRegister() async {
    if (!_validate()) return;

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final newUser = User(
      username: _usernameController.text.trim(),
      password: _passwordController.text,
      phone: _phoneController.text.trim(),
      address: _addressController.text.trim(),
    );

    final ok = await widget.controller.register(newUser);

    if (!mounted) return;
    setState(() => _isLoading = false);

    if (ok) {
      widget.onRegisterSuccess();
    } else {
      setState(() => _errorMessage = 'Không thể lưu tài khoản. Vui lòng thử lại.');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Column(
        children: [
          // Header (đúng phong cách App_design Register)
          Container(
            width: double.infinity,
            padding: const EdgeInsets.fromLTRB(16, 52, 20, 24),
            color: AppColors.primaryRed,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                IconButton(
                  onPressed: widget.onGoLogin,
                  icon: const Icon(Icons.arrow_back_rounded, color: Colors.white),
                  padding: EdgeInsets.zero,
                  alignment: Alignment.centerLeft,
                ),
                const SizedBox(height: 8),
                const Text(
                  'Tạo tài khoản',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 24,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Điền đầy đủ thông tin bên dưới',
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.8),
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),

          // Form Body
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildInput(
                    label: 'Tên đăng nhập',
                    hint: 'Ít nhất 3 ký tự, không dấu',
                    controller: _usernameController,
                  ),
                  const SizedBox(height: 14),

                  _buildInput(
                    label: 'Mật khẩu',
                    hint: 'Tối thiểu 6 ký tự',
                    controller: _passwordController,
                    isPassword: true,
                    showPassword: _showPassword,
                    onTogglePassword: () => setState(() => _showPassword = !_showPassword),
                  ),
                  const SizedBox(height: 14),

                  _buildInput(
                    label: 'Xác nhận mật khẩu',
                    hint: 'Nhập lại mật khẩu',
                    controller: _confirmPasswordController,
                    isPassword: true,
                    showPassword: _showConfirm,
                    onTogglePassword: () => setState(() => _showConfirm = !_showConfirm),
                  ),
                  const SizedBox(height: 14),

                  _buildInput(
                    label: 'Số điện thoại',
                    hint: 'vd: 0901234567',
                    controller: _phoneController,
                    keyboardType: TextInputType.phone,
                  ),
                  const SizedBox(height: 14),

                  _buildInput(
                    label: 'Địa chỉ thường trú',
                    hint: 'Số nhà, tên đường, phường/xã...',
                    controller: _addressController,
                    maxLines: 2,
                  ),

                  if (_errorMessage != null) ...[
                    const SizedBox(height: 14),
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: const Color(0xFFFEF2F2),
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: const Color(0xFFFECACA)),
                      ),
                      child: Text(
                        _errorMessage!,
                        style: const TextStyle(
                          color: Color(0xFFB91C1C),
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],

                  const SizedBox(height: 24),

                  // Nút Tạo tài khoản
                  SizedBox(
                    width: double.infinity,
                    height: 52,
                    child: ElevatedButton(
                      onPressed: _isLoading ? null : _handleRegister,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.primaryRed,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16),
                        ),
                        elevation: 0,
                      ),
                      child: _isLoading
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                color: Colors.white,
                                strokeWidth: 2,
                              ),
                            )
                          : const Text(
                              'Tạo tài khoản',
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: 16,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                    ),
                  ),

                  const SizedBox(height: 16),

                  // Đã có tài khoản
                  Center(
                    child: TextButton(
                      onPressed: widget.onGoLogin,
                      child: const Text(
                        'Đã có tài khoản? Đăng nhập ngay',
                        style: TextStyle(
                          color: Color(0xFF4B5563),
                          fontSize: 13,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInput({
    required String label,
    required String hint,
    required TextEditingController controller,
    bool isPassword = false,
    bool showPassword = false,
    VoidCallback? onTogglePassword,
    TextInputType keyboardType = TextInputType.text,
    int maxLines = 1,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w800,
            color: Color(0xFF374151),
          ),
        ),
        const SizedBox(height: 6),
        TextField(
          controller: controller,
          obscureText: isPassword && !showPassword,
          keyboardType: keyboardType,
          maxLines: maxLines,
          decoration: InputDecoration(
            hintText: hint,
            hintStyle: const TextStyle(fontSize: 14, color: Color(0xFF9CA3AF)),
            filled: true,
            fillColor: const Color(0xFFF9FAFB),
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(16),
              borderSide: const BorderSide(color: Color(0xFFE5E7EB)),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(16),
              borderSide: const BorderSide(color: Color(0xFFE5E7EB)),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(16),
              borderSide: const BorderSide(color: AppColors.primaryRed, width: 1.5),
            ),
            suffixIcon: isPassword
                ? IconButton(
                    icon: Icon(
                      showPassword ? Icons.visibility_off : Icons.visibility,
                      color: const Color(0xFF9CA3AF),
                      size: 20,
                    ),
                    onPressed: onTogglePassword,
                  )
                : null,
          ),
        ),
      ],
    );
  }
}
