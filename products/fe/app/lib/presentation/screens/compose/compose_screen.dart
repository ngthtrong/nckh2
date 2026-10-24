import 'dart:async';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../../../core/constants/app_colors.dart';
import '../../../config.dart';
import '../../../domain/usecases/submit_rescue_post_usecase.dart';
import '../../../core/platform/local_file.dart';
import '../../../domain/entities/ai_tag.dart';
import '../../controllers/app_controller.dart';
import '../../widgets/emergency_condition_selector.dart';
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
  bool _cannotMove = false;
  List<String> _severeSigns = [];
  final TextEditingController _descController = TextEditingController();

  String? _imagePath;
  List<AiTag> _aiTags = [];
  bool _isAnalyzing = false;
  int _analysisGeneration = 0;
  bool _isSubmitting = false;
  bool _isPicking = false;
  String? _submissionError;

  @override
  void initState() {
    super.initState();
    final draft = widget.controller.composeDraft;
    if (draft != null) {
      _trappedCount = (draft['trappedCount'] as num?)?.toInt() ?? 0;
      _injuredCount = (draft['injuredCount'] as num?)?.toInt() ?? 0;
      _vulnerableGroups = List<String>.from(
        draft['vulnerableGroups'] as List? ?? [],
      );
      _cannotMove = draft['cannotMove'] == true;
      _severeSigns = List<String>.from(draft['severeSigns'] as List? ?? []);
      _descController.text = draft['description'] as String? ?? '';
      _imagePath = draft['imagePath'] as String?;
      _submissionError = draft['recoveryError'] as String?;
      if (_imagePath != null && !localFileExists(_imagePath!)) {
        _imagePath = null;
        _submissionError =
            'Ảnh của bản nháp không còn. Nội dung được giữ; hãy chọn lại ảnh.';
      }
    }
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      unawaited(widget.controller.ensureModelLoaded());
      if (_imagePath != null) unawaited(_analyzePhoto(_imagePath!));
    });
  }

  Map<String, dynamic> _draft() => {
    'trappedCount': _trappedCount,
    'injuredCount': _injuredCount,
    'vulnerableGroups': List<String>.of(_vulnerableGroups),
    'cannotMove': _cannotMove,
    'severeSigns': List<String>.of(_severeSigns),
    'description': _descController.text,
    'imagePath': _imagePath,
  };

  Future<void> _pickPhoto(ImageSource source) async {
    if (_isPicking || _isSubmitting) return;
    setState(() => _isPicking = true);
    final previousPath = _imagePath;
    String? path;
    try {
      await widget.controller.saveComposeDraft(_draft());
      if (!mounted) return;
      path = await widget.controller.pickImage(source: source);
      if (!mounted || path == null) return;
      setState(() {
        _analysisGeneration++;
        _imagePath = path;
        _aiTags = [];
        _isAnalyzing = false;
      });
    } catch (_) {
      if (mounted) {
        setState(
          () => _submissionError =
              'Chưa lưu được ảnh/bản nháp. Nội dung form được giữ; hãy thử lại.',
        );
      }
    } finally {
      try {
        await widget.controller.clearComposeDraft();
      } catch (_) {
        debugPrint('Chưa xóa được bản lưu tạm của trình chọn ảnh.');
      }
      if (path != null && path != previousPath) {
        await widget.controller.discardComposeImage(previousPath);
      }
      if (!mounted) {
        await widget.controller.discardComposeImage(path);
        if (path == null) {
          await widget.controller.discardComposeImage(previousPath);
        }
      }
      if (mounted) setState(() => _isPicking = false);
    }
    if (mounted && path != null) await _analyzePhoto(path);
  }

  Future<void> _analyzePhoto(String path) async {
    final generation = ++_analysisGeneration;
    setState(() {
      _aiTags = [];
      _isAnalyzing = true;
    });
    final tags = await widget.controller.analyzeImage(path);
    if (mounted && generation == _analysisGeneration) {
      setState(() {
        _aiTags = tags;
        _isAnalyzing = false;
      });
    }
  }

  Future<void> _handleSubmit() async {
    if (_isSubmitting || _isPicking) return;
    setState(() {
      _isSubmitting = true;
      _submissionError = null;
    });

    // A recovered picker snapshot must not outlive a submitted report.
    try {
      await widget.controller.clearComposeDraft();
    } catch (_) {
      if (mounted) {
        setState(() {
          _isSubmitting = false;
          _submissionError = 'Chưa xóa được bản lưu tạm. Hãy thử gửi lại.';
        });
      }
      return;
    }
    final record = await widget.controller.submitPost(
      trappedCount: _trappedCount,
      injuredCount: _injuredCount,
      vulnerableGroups: _vulnerableGroups,
      cannotMove: _cannotMove,
      severeSigns: _severeSigns,
      description: _descController.text.trim(),
      imagePath: _imagePath,
      aiTags: _aiTags,
    );

    if (record != null) {
      try {
        await widget.controller.clearComposeDraft();
      } catch (_) {
        debugPrint('Chưa xóa được bản nháp đã gửi.');
      }
      await widget.controller.discardComposeImage(_imagePath);
      if (!mounted) return;
      widget.onSuccess();
    } else if (mounted) {
      setState(() {
        _isSubmitting = false;
        _submissionError =
            widget.controller.submissionError ??
            'Chưa gửi được báo cáo. Nội dung form vẫn được giữ; hãy thử lại.';
      });
    } else {
      await widget.controller.discardComposeImage(_imagePath);
    }
  }

  Future<void> _leaveForm() async {
    if (_isSubmitting || _isPicking) return;
    setState(() => _isPicking = true);
    try {
      await widget.controller.clearComposeDraft();
      await widget.controller.discardComposeImage(_imagePath);
      if (mounted) widget.onBack();
    } catch (_) {
      if (mounted) {
        setState(() {
          _isPicking = false;
          _submissionError =
              'Chưa xóa được bản lưu tạm. Hãy thử đóng lại form.';
        });
      }
    }
  }

  Future<void> _removePhoto() async {
    final path = _imagePath;
    setState(() {
      _isPicking = true;
      _analysisGeneration++;
      _imagePath = null;
      _aiTags = [];
      _isAnalyzing = false;
    });
    try {
      await widget.controller.clearComposeDraft();
      await widget.controller.discardComposeImage(path);
    } catch (_) {
      debugPrint('Chưa dọn được ảnh vừa bỏ khỏi form.');
    } finally {
      if (mounted) setState(() => _isPicking = false);
    }
  }

  Future<void> _discardDisposedPhoto() async {
    try {
      await widget.controller.clearComposeDraft();
    } catch (_) {
      debugPrint('Chưa xóa được snapshot của form đã đóng.');
    }
    await widget.controller.discardComposeImage(_imagePath);
  }

  @override
  void dispose() {
    if (!_isPicking && !_isSubmitting) {
      unawaited(_discardDisposedPhoto());
    }
    _descController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final inputError = SubmitRescuePostUseCase.validateInput(
      trappedCount: _trappedCount,
      injuredCount: _injuredCount,
      description: _descController.text.trim(),
    );
    final canSubmit =
        (_trappedCount > 0 ||
            _injuredCount > 0 ||
            _vulnerableGroups.isNotEmpty ||
            _cannotMove ||
            _severeSigns.isNotEmpty ||
            _descController.text.trim().isNotEmpty ||
            _imagePath != null) &&
        !_isSubmitting &&
        !_isPicking &&
        inputError == null;

    final scaffold = Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Column(
          children: [
            ScreenHeader(
              title: 'Gửi bài cứu hộ',
              onBack: _isSubmitting || _isPicking ? null : _leaveForm,
              action: ElevatedButton(
                onPressed: canSubmit ? _handleSubmit : null,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primaryRed,
                  disabledBackgroundColor: AppColors.primaryRed.withValues(
                    alpha: 0.4,
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
            if (_submissionError != null)
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
                child: Text(
                  _submissionError!,
                  style: const TextStyle(color: AppColors.primaryRed),
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

                    EmergencyConditionSelector(
                      cannotMove: _cannotMove,
                      severeSigns: _severeSigns,
                      onCannotMoveChanged: (value) =>
                          setState(() => _cannotMove = value),
                      onSevereSignsChanged: (values) =>
                          setState(() => _severeSigns = values),
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
                      maxLength: kMaxDescriptionCharacters,
                      decoration: InputDecoration(
                        errorText: inputError,
                        counterText:
                            '${SubmitRescuePostUseCase.descriptionWordCount(_descController.text)}/$kMaxDescriptionWords từ · ${_descController.text.runes.length}/$kMaxDescriptionCharacters ký tự',
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
                              onTap: _removePhoto,
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
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) {
        if (!didPop && !_isSubmitting && !_isPicking) unawaited(_leaveForm());
      },
      child: AbsorbPointer(
        absorbing: _isSubmitting || _isPicking,
        child: ExcludeFocus(
          excluding: _isSubmitting || _isPicking,
          child: scaffold,
        ),
      ),
    );
  }
}
