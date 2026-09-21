import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../controllers/rescue_controller.dart';
import '../domain/report.dart';
import '../widgets/sms_confirmation_button.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, required this.controller});

  final RescueController controller;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  var _page = 0;

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: widget.controller,
      builder: (context, _) {
        final wide = MediaQuery.sizeOf(context).width >= 900;
        final content = _page == 0
            ? ComposePanel(controller: widget.controller)
            : HistoryPanel(controller: widget.controller);
        return Scaffold(
          body: SafeArea(
            child: Row(
              children: [
                if (wide)
                  NavigationRail(
                    backgroundColor: const Color(0xFF183153),
                    selectedIndex: _page,
                    onDestinationSelected: (value) => setState(() => _page = value),
                    labelType: NavigationRailLabelType.all,
                    leading: const Padding(
                      padding: EdgeInsets.symmetric(vertical: 20),
                      child: Icon(Icons.flood, color: Colors.white, size: 34),
                    ),
                    destinations: const [
                      NavigationRailDestination(
                        icon: Icon(Icons.add_alert_outlined, color: Colors.white70),
                        selectedIcon: Icon(Icons.add_alert, color: Colors.white),
                        label: Text('Báo cáo', style: TextStyle(color: Colors.white)),
                      ),
                      NavigationRailDestination(
                        icon: Icon(Icons.history, color: Colors.white70),
                        selectedIcon: Icon(Icons.history, color: Colors.white),
                        label: Text('Lịch sử', style: TextStyle(color: Colors.white)),
                      ),
                    ],
                  ),
                Expanded(child: content),
              ],
            ),
          ),
          bottomNavigationBar: wide
              ? null
              : NavigationBar(
                  selectedIndex: _page,
                  onDestinationSelected: (value) => setState(() => _page = value),
                  destinations: const [
                    NavigationDestination(icon: Icon(Icons.add_alert), label: 'Báo cáo'),
                    NavigationDestination(icon: Icon(Icons.history), label: 'Lịch sử'),
                  ],
                ),
        );
      },
    );
  }
}

class ComposePanel extends StatefulWidget {
  const ComposePanel({super.key, required this.controller});

  final RescueController controller;

  @override
  State<ComposePanel> createState() => _ComposePanelState();
}

class _ComposePanelState extends State<ComposePanel> {
  final _description = TextEditingController();
  final _trapped = TextEditingController(text: '0');
  final _injured = TextEditingController(text: '0');

  @override
  void dispose() {
    _description.dispose();
    _trapped.dispose();
    _injured.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final controller = widget.controller;
    return CustomScrollView(
      slivers: [
        SliverToBoxAdapter(child: _Header(controller: controller)),
        SliverToBoxAdapter(
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 1050),
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 24, 20, 48),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    _CapabilityStrip(controller: controller),
                    const SizedBox(height: 20),
                    Text('Phiếu báo cáo hiện trường', style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w800, color: const Color(0xFF183153))),
                    const SizedBox(height: 6),
                    const Text('Ảnh và kết quả AI được xử lý trên thiết bị. Báo cáo được lưu trước khi gửi.'),
                    const SizedBox(height: 22),
                    LayoutBuilder(
                      builder: (context, constraints) {
                        final horizontal = constraints.maxWidth > 720;
                        final form = _FormFields(description: _description, trapped: _trapped, injured: _injured, onLocate: controller.locate, location: controller.position == null ? 'Chưa lấy vị trí' : '${controller.position!.latitude.toStringAsFixed(6)}, ${controller.position!.longitude.toStringAsFixed(6)}');
                        final image = _ImagePanel(controller: controller);
                        return horizontal
                            ? Row(crossAxisAlignment: CrossAxisAlignment.start, children: [Expanded(child: form), const SizedBox(width: 22), Expanded(child: image)])
                            : Column(children: [form, const SizedBox(height: 18), image]);
                      },
                    ),
                    if (controller.message != null) ...[
                      const SizedBox(height: 16),
                      MaterialBanner(
                        content: Text(controller.message!),
                        leading: const Icon(Icons.info_outline),
                        actions: [TextButton(onPressed: () {}, child: const Text('Đã hiểu'))],
                      ),
                    ],
                    const SizedBox(height: 20),
                    FilledButton.icon(
                      onPressed: controller.submitting
                          ? null
                          : () async {
                              await controller.submit(
                                description: _description.text,
                                trappedCount: int.tryParse(_trapped.text) ?? 0,
                                injuredCount: int.tryParse(_injured.text) ?? 0,
                              );
                              if (mounted) _description.clear();
                            },
                      style: FilledButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 18)),
                      icon: controller.submitting
                          ? const SizedBox.square(dimension: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                          : const Icon(Icons.send),
                      label: const Text('Lưu và gửi báo cáo'),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.controller});
  final RescueController controller;

  @override
  Widget build(BuildContext context) => Container(
    color: const Color(0xFFB42318),
    padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 18),
    child: Row(children: [
      const Icon(Icons.emergency, color: Colors.white, size: 30),
      const SizedBox(width: 12),
      const Expanded(child: Text('Cứu hộ lũ lụt', style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.w800))),
      Text('${controller.reports.where((r) => r.syncState == SyncState.pending).length} chờ gửi', style: const TextStyle(color: Colors.white)),
    ]),
  );
}

class _CapabilityStrip extends StatelessWidget {
  const _CapabilityStrip({required this.controller});
  final RescueController controller;

  @override
  Widget build(BuildContext context) => Container(
    decoration: const BoxDecoration(color: Color(0xFFE7EEF2), border: Border(left: BorderSide(color: Color(0xFF2D6A8A), width: 5))),
    padding: const EdgeInsets.all(14),
    child: Wrap(spacing: 18, runSpacing: 8, children: [
      _status(Icons.memory, 'AI cục bộ', !controller.initializing),
      _status(Icons.cloud_outlined, 'Backend', controller.backendAvailable),
      _status(Icons.sms_outlined, 'SMS', controller.smsEnabled),
      TextButton.icon(onPressed: controller.retrySync, icon: const Icon(Icons.sync), label: const Text('Đồng bộ lại')),
    ]),
  );

  Widget _status(IconData icon, String label, bool ready) => Row(mainAxisSize: MainAxisSize.min, children: [
    Icon(icon, size: 18, color: ready ? const Color(0xFF18794E) : const Color(0xFF9A6700)),
    const SizedBox(width: 6), Text('$label: ${ready ? 'sẵn sàng' : 'chưa sẵn sàng'}'),
  ]);
}

class _FormFields extends StatelessWidget {
  const _FormFields({required this.description, required this.trapped, required this.injured, required this.onLocate, required this.location});
  final TextEditingController description;
  final TextEditingController trapped;
  final TextEditingController injured;
  final Future<void> Function() onLocate;
  final String location;

  @override
  Widget build(BuildContext context) => Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
    TextField(controller: description, maxLines: 5, decoration: const InputDecoration(labelText: 'Mô tả tình hình', hintText: 'Mức nước, mốc đường và tình trạng người cần cứu...')),
    const SizedBox(height: 14),
    Row(children: [
      Expanded(child: TextField(controller: trapped, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Người mắc kẹt'))),
      const SizedBox(width: 12),
      Expanded(child: TextField(controller: injured, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Người bị thương'))),
    ]),
    const SizedBox(height: 14),
    OutlinedButton.icon(onPressed: onLocate, icon: const Icon(Icons.my_location), label: Text(location)),
  ]);
}

class _ImagePanel extends StatelessWidget {
  const _ImagePanel({required this.controller});
  final RescueController controller;

  @override
  Widget build(BuildContext context) => Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
    Container(
      height: 220,
      color: const Color(0xFFDDE7EB),
      child: controller.imageBytes == null
          ? const Center(child: Column(mainAxisSize: MainAxisSize.min, children: [Icon(Icons.add_a_photo_outlined, size: 42, color: Color(0xFF2D6A8A)), SizedBox(height: 8), Text('Thêm ảnh hiện trường')]))
          : Image.memory(controller.imageBytes!, fit: BoxFit.cover),
    ),
    const SizedBox(height: 10),
    Row(children: [
      Expanded(child: OutlinedButton.icon(onPressed: () => controller.pickImage(ImageSource.camera), icon: const Icon(Icons.camera_alt), label: const Text('Chụp ảnh'))),
      const SizedBox(width: 8),
      Expanded(child: OutlinedButton.icon(onPressed: () => controller.pickImage(ImageSource.gallery), icon: const Icon(Icons.photo_library_outlined), label: const Text('Chọn ảnh'))),
    ]),
    const SizedBox(height: 12),
    if (controller.analyzing) const LinearProgressIndicator(),
    if (controller.inferenceResult case final result?)
      Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(color: const Color(0xFF183153), border: Border(left: BorderSide(color: _levelColor(result.label), width: 10))),
        child: Row(children: [
          Expanded(child: Text(_label(result.label), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 16))),
          Text('${(result.confidence * 100).toStringAsFixed(1)}%\n${result.executionProvider}', textAlign: TextAlign.right, style: const TextStyle(color: Colors.white)),
        ]),
      ),
  ]);
}

class HistoryPanel extends StatelessWidget {
  const HistoryPanel({super.key, required this.controller});
  final RescueController controller;

  @override
  Widget build(BuildContext context) => Column(children: [
    _Header(controller: controller),
    Expanded(
      child: controller.reports.isEmpty
          ? const Center(child: Text('Chưa có báo cáo. Hãy tạo phiếu hiện trường đầu tiên.'))
          : ListView.separated(
              padding: const EdgeInsets.all(20),
              itemCount: controller.reports.length,
              separatorBuilder: (_, _) => const Divider(height: 1),
              itemBuilder: (context, index) => _ReportRow(report: controller.reports[index], controller: controller),
            ),
    ),
  ]);
}

class _ReportRow extends StatefulWidget {
  const _ReportRow({required this.report, required this.controller});
  final RescueReport report;
  final RescueController controller;

  @override
  State<_ReportRow> createState() => _ReportRowState();
}

class _ReportRowState extends State<_ReportRow> {
  final recipient = TextEditingController();
  @override
  void dispose() { recipient.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 16),
    child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
      CircleAvatar(backgroundColor: widget.report.syncState == SyncState.synced ? const Color(0xFF18794E) : const Color(0xFFE9A23B), child: Icon(widget.report.syncState == SyncState.synced ? Icons.check : Icons.schedule, color: Colors.white)),
      const SizedBox(width: 14),
      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(widget.report.description.isEmpty ? 'Báo cáo ${widget.report.id.substring(0, 8)}' : widget.report.description, style: const TextStyle(fontWeight: FontWeight.w700)),
        const SizedBox(height: 4),
        Text('${widget.report.trappedCount} mắc kẹt · ${widget.report.injuredCount} bị thương · ${widget.report.aiLabel ?? 'chưa có AI'}'),
        if (widget.report.syncError != null) Text(widget.report.syncError!, style: const TextStyle(color: Color(0xFFB42318))),
        if (widget.controller.smsEnabled && widget.report.syncState == SyncState.synced) ...[
          const SizedBox(height: 10),
          SizedBox(width: 260, child: TextField(controller: recipient, onChanged: (_) => setState(() {}), decoration: const InputDecoration(labelText: 'Số nhận, ví dụ +849...'))),
          const SizedBox(height: 8),
          if (recipient.text.startsWith('+') && recipient.text.length >= 9)
            SmsConfirmationButton(recipient: recipient.text, onConfirmed: () => widget.controller.sendSms(widget.report, recipient.text))
          else
            const Text('Nhập số quốc tế bắt đầu bằng dấu + để bật nút SMS.'),
        ],
      ])),
    ]),
  );
}

String _label(String label) => switch (label) {
  'low' => 'Ngập nhẹ', 'medium' => 'Ngập trung bình', 'high' => 'Ngập sâu nguy hiểm', _ => 'Không ngập',
};

Color _levelColor(String label) => switch (label) {
  'low' => const Color(0xFFE9A23B), 'medium' => const Color(0xFFEA6A2A), 'high' => const Color(0xFFEF4444), _ => const Color(0xFF18794E),
};
