import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/platform/local_file.dart';
import '../../../domain/entities/ai_tag.dart';
import '../../controllers/app_controller.dart';
import '../../widgets/number_stepper_input.dart';
import '../../widgets/screen_header.dart';
import '../../widgets/tag_chip.dart';
import '../../widgets/vulnerable_group_selector.dart';

class ComposeScreen extends StatefulWidget {
  final AppController controller;
  final VoidCallback onBack;
  final VoidCallback onSuccess;

  const ComposeScreen({
    super.key,
    required this.controller,
    required this.onBack,
    required this.onSuccess,
  });

  @override
  State<ComposeScreen> createState() => _ComposeScreenState();
}

class _ComposeScreenState extends State<ComposeScreen> {
  int _trappedCount = 0;
  int _injuredCount = 0;
  List<String> _vulnerableGroups = [];
  final TextEditingController _descController = TextEditingController();

  String? _imagePath;
  List<AiTag> _aiTags = [];
  bool _isAnalyzing = false;
  bool _isSubmitting = false;

  Future<void> _pickPhoto(ImageSource source) async {
    final path = await widget.controller.pickImage(source: source);
    if (path != null) {
      setState(() {
        _imagePath = path;
        _isAnalyzing = true;
      });

      final tags = await widget.controller.analyzeImage(path);
      if (mounted) {
        setState(() {
          _aiTags = tags;
          _isAnalyzing = false;
        });
      }
    }
  }

  Future<void> _handleSubmit() async {
    if (_isSubmitting) return;
    setState(() => _isSubmitting = true);

    final record = await widget.controller.submitPost(
      trappedCount: _trappedCount,
      injuredCount: _injuredCount,
      vulnerableGroups: _vulnerableGroups,
      description: _descController.text.trim(),
      imagePath: _imagePath,
      aiTags: _aiTags,
    );

    if (mounted) {
      setState(() => _isSubmitting = false);
      if (record != null) {
        widget.onSuccess();
      }
    }
  }

  @override
  void dispose() {
    _descController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final canSubmit =
        (_trappedCount > 0 ||
            _injuredCount > 0 ||
            _vulnerableGroups.isNotEmpty ||
            _descController.text.trim().isNotEmpty ||
            _imagePath != null) &&
        !_isSubmitting;

    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Column(
          children: [
            ScreenHeader(
              title: 'Gửi bài cứu hộ',
              onBack: widget.onBack,
              action: ElevatedButton(
                onPressed: canSubmit ? _handleSubmit : null,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primaryRed,
                  disabledBackgroundColor: AppColors.primaryRed.withOpacity(
                    0.4,
                  ),
                  elevation: 0,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(20),
                  ),
                  padding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 8,
                  ),
                ),
                child: _isSubmitting
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(
                          color: Colors.white,
                          strokeWidth: 2,
                        ),
                      )
                    : const Text(
                        'Gửi ngay',
                        style: TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w800,
                          fontSize: 13,
                        ),
                      ),
              ),
            ),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                physics: const BouncingScrollPhysics(),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Location bar
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 14,
                        vertical: 10,
                      ),
                      decoration: BoxDecoration(
                        color: const Color(0xFFFEF2F2),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: const Color(0xFFFECACA)),
                      ),
                      child: Row(
                        children: [
                          const Icon(
                            Icons.location_on,
                            color: AppColors.primaryRed,
                            size: 18,
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              widget.controller.locationLabel,
                              style: const TextStyle(
                                color: Color(0xFF991B1B),
                                fontSize: 12,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ),
                          const Text(
                            'Tự động',
                            style: TextStyle(
                              color: Color(0xFFF87171),
                              fontSize: 11,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 18),

                    // Trapped & Injured count inputs
                    const Text(
                      'SỐ LƯỢNG NGƯỜI CẦN CỨU HỘ',
                      style: TextStyle(
                        color: Color(0xFF6B7280),
                        fontSize: 11,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 1.2,
                      ),
                    ),
                    const SizedBox(height: 10),
                    NumberStepperInput(
                      label: 'Số người mắc kẹt',
                      value: _trappedCount,
                      icon: Icons.warning_amber_rounded,
                      onChanged: (val) => setState(() => _trappedCount = val),
                    ),
                    const SizedBox(height: 10),
                    NumberStepperInput(
                      label: 'Số người bị thương',
                      value: _injuredCount,
                      icon: Icons.local_hospital_outlined,
                      onChanged: (val) => setState(() => _injuredCount = val),
                    ),
                    const SizedBox(height: 18),

                    // Vulnerable Group selector
                    VulnerableGroupSelector(
                      selectedGroups: _vulnerableGroups,
                      onChanged: (groups) =>
                          setState(() => _vulnerableGroups = groups),
                    ),
                    const SizedBox(height: 18),

                    // Detailed Notes
                    const Text(
                      'GHI CHÚ / MÔ TẢ CHI TIẾT',
                      style: TextStyle(
                        color: Color(0xFF6B7280),
                        fontSize: 11,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 1.2,
                      ),
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: _descController,
                      maxLines: 4,
                      maxLength: 300,
                      decoration: InputDecoration(
                        hintText:
                            'Ghi rõ: ở đâu, gần cột điện/mốc đường nào, mức độ ngập nước hay tình trạng khẩn cấp...',
                        hintStyle: const TextStyle(
                          color: Color(0xFF9CA3AF),
                          fontSize: 13,
                        ),
                        filled: true,
                        fillColor: const Color(0xFFF9FAFB),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(16),
                          borderSide: const BorderSide(
                            color: Color(0xFFE5E7EB),
                          ),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(16),
                          borderSide: const BorderSide(
                            color: Color(0xFFE5E7EB),
                          ),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(16),
                          borderSide: const BorderSide(
                            color: AppColors.primaryRed,
                          ),
                        ),
                        contentPadding: const EdgeInsets.all(14),
                      ),
                      style: const TextStyle(
                        fontSize: 14,
                        color: Color(0xFF1F2937),
                      ),
                      onChanged: (_) => setState(() {}),
                    ),
                    const SizedBox(height: 12),

                    // Scene Image Picker
                    const Text(
                      'ẢNH HIỆN TRƯỜNG',
                      style: TextStyle(
                        color: Color(0xFF6B7280),
                        fontSize: 11,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 1.2,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        ElevatedButton.icon(
                          onPressed: () => _pickPhoto(ImageSource.camera),
                          icon: const Icon(Icons.camera_alt, size: 18),
                          label: const Text('Chụp ảnh'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFFF3F4F6),
                            foregroundColor: const Color(0xFF374151),
                            elevation: 0,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(14),
                            ),
                          ),
                        ),
                        const SizedBox(width: 10),
                        OutlinedButton.icon(
                          onPressed: () => _pickPhoto(ImageSource.gallery),
                          icon: const Icon(Icons.photo_library, size: 18),
                          label: const Text('Chọn từ máy'),
                          style: OutlinedButton.styleFrom(
                            foregroundColor: const Color(0xFF374151),
                            side: const BorderSide(color: Color(0xFFD1D5DB)),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(14),
                            ),
                          ),
                        ),
                      ],
                    ),
                    if (_imagePath != null) ...[
                      const SizedBox(height: 12),
                      Stack(
                        children: [
                          ClipRRect(
                            borderRadius: BorderRadius.circular(16),
                            child: Image(
                              image: localImageProvider(_imagePath!),
                              height: 160,
                              width: double.infinity,
                              fit: BoxFit.cover,
                            ),
                          ),
                          Positioned(
                            top: 8,
                            right: 8,
                            child: GestureDetector(
                              onTap: () => setState(() {
                                _imagePath = null;
                                _aiTags = [];
                              }),
                              child: Container(
                                padding: const EdgeInsets.all(6),
                                decoration: const BoxDecoration(
                                  color: Colors.black54,
                                  shape: BoxShape.circle,
                                ),
                                child: const Icon(
                                  Icons.close,
                                  color: Colors.white,
                                  size: 16,
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                    const SizedBox(height: 18),

                    // AI Recognition Panel
                    if (_isAnalyzing || _aiTags.isNotEmpty) ...[
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFFF7ED),
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: const Color(0xFFFED7AA)),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                const Icon(
                                  Icons.psychology,
                                  color: Color(0xFFC2410C),
                                  size: 20,
                                ),
                                const SizedBox(width: 6),
                                const Text(
                                  'AI NHẬN DIỆN HIỆN TRƯỜNG',
                                  style: TextStyle(
                                    color: Color(0xFFC2410C),
                                    fontSize: 11,
                                    fontWeight: FontWeight.w800,
                                    letterSpacing: 1.2,
                                  ),
                                ),
                                if (_isAnalyzing) ...[
                                  const Spacer(),
                                  const SizedBox(
                                    width: 14,
                                    height: 14,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                      color: Color(0xFFC2410C),
                                    ),
                                  ),
                                ],
                              ],
                            ),
                            const SizedBox(height: 10),
                            if (_isAnalyzing)
                              const Text(
                                'Đang phân tích hình ảnh on-device...',
                                style: TextStyle(
                                  color: Color(0xFFEA580C),
                                  fontSize: 12,
                                  fontWeight: FontWeight.w600,
                                ),
                              )
                            else ...[
                              Wrap(
                                spacing: 6,
                                runSpacing: 6,
                                children: _aiTags
                                    .map((t) => TagChip(tag: t))
                                    .toList(),
                              ),
                              if (widget.controller.latestComparison !=
                                  null) ...[
                                const SizedBox(height: 10),
                                Text(
                                  'ONNX ${widget.controller.latestComparison!.durationMsOnnx} ms · '
                                  'PTE ${widget.controller.latestComparison!.durationMsPte} ms · '
                                  '${widget.controller.latestComparison!.isIdentical ? 'cùng nhãn' : 'khác nhãn'}',
                                  style: const TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.w700,
                                    color: Color(0xFF9A3412),
                                  ),
                                ),
                              ],
                            ],
                          ],
                        ),
                      ),
                      const SizedBox(height: 18),
                    ],

                    // Tips Panel
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: const Color(0xFFF9FAFB),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: const Color(0xFFF3F4F6)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: const [
                          Text(
                            'MẸO GỬI BÀI HIỆU QUẢ',
                            style: TextStyle(
                              color: Color(0xFF6B7280),
                              fontSize: 11,
                              fontWeight: FontWeight.w800,
                              letterSpacing: 1.2,
                            ),
                          ),
                          SizedBox(height: 8),
                          Text(
                            '1. Điền chính xác số lượng người cần hỗ trợ.',
                            style: TextStyle(
                              color: Color(0xFF4B5563),
                              fontSize: 12,
                            ),
                          ),
                          SizedBox(height: 4),
                          Text(
                            '2. Chụp ảnh rõ toàn cảnh hiện trường.',
                            style: TextStyle(
                              color: Color(0xFF4B5563),
                              fontSize: 12,
                            ),
                          ),
                          SizedBox(height: 4),
                          Text(
                            '3. Mô tả các địa điểm mốc gần nhất (ví dụ: gần nhà văn hóa, cây xăng...).',
                            style: TextStyle(
                              color: Color(0xFF4B5563),
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
