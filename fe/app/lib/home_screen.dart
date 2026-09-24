import 'package:flutter/material.dart';

import 'controller.dart';
import 'models/rescue_record.dart';
import 'send_mode.dart';

const _red = Color(0xFFC62828);
const _redDark = Color(0xFF8E0000);
const _surface = Color(0xFFF7F7F7);

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, required this.controller});

  final AppController controller;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  late final AppController _c;
  int _tab = 0;
  String _guideTab = 'Dùng app';

  @override
  void initState() {
    super.initState();
    _c = widget.controller;
    _c.addListener(_onChange);
    _c.init();
  }

  void _onChange() => setState(() {});

  @override
  void dispose() {
    _c.removeListener(_onChange);
    _c.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    if (!_c.busy) await _c.sos();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _surface,
      body: SafeArea(
        bottom: false,
        child: IndexedStack(
          index: _tab,
          children: [_buildHome(), _buildHistory(), _buildGuide()],
        ),
      ),
      bottomNavigationBar: _buildNavigation(),
    );
  }

  Widget _buildHome() {
    return CustomScrollView(
      slivers: [
        SliverToBoxAdapter(child: _buildHeader()),
        SliverToBoxAdapter(child: _buildSos()),
        SliverToBoxAdapter(child: _buildComposeCta()),
        SliverToBoxAdapter(child: _buildHomeContent()),
      ],
    );
  }

  Widget _buildHeader() {
    final ready = _c.modelReady && _c.netLabel != 'none';
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 26, 20, 18),
      color: _red,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'HỆ THỐNG',
                      style: TextStyle(
                        color: Colors.white60,
                        fontSize: 11,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 1.5,
                      ),
                    ),
                    SizedBox(height: 4),
                    Text(
                      'Cứu Hộ Khẩn Cấp',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 25,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 11,
                  vertical: 9,
                ),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: .15),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Row(
                  children: [
                    Icon(
                      Icons.circle,
                      size: 10,
                      color: ready ? Colors.greenAccent : Colors.amberAccent,
                    ),
                    const SizedBox(width: 7),
                    Text(
                      ready ? 'Sẵn sàng' : 'Đang nạp',
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w800,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 10),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: .11),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                const Icon(Icons.location_on, color: Colors.white70, size: 17),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'GPS tự động · Mạng ${_c.netLabel}',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                Icon(
                  _c.netLabel == 'none'
                      ? Icons.signal_wifi_off
                      : Icons.signal_wifi_4_bar,
                  color: Colors.white70,
                  size: 17,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSos() {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 23),
      color: const Color(0xFFFFF3F3),
      child: Column(
        children: [
          const Text(
            'Nhấn SOS để gọi cứu hộ ngay',
            style: TextStyle(
              color: Colors.black54,
              fontSize: 14,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 4),
          const Text(
            'Vị trí GPS sẽ được gửi tự động',
            style: TextStyle(color: Colors.black38, fontSize: 12),
          ),
          const SizedBox(height: 18),
          Stack(
            alignment: Alignment.center,
            children: [
              Container(
                width: 138,
                height: 138,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: _red.withValues(alpha: .10),
                ),
              ),
              Container(
                width: 116,
                height: 116,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: _red.withValues(alpha: .16),
                ),
              ),
              Material(
                color: _c.busy ? _redDark : _red,
                shape: const CircleBorder(),
                elevation: 8,
                child: InkWell(
                  customBorder: const CircleBorder(),
                  onTap: _c.busy ? null : _send,
                  child: SizedBox(
                    width: 94,
                    height: 94,
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        if (_c.busy)
                          const SizedBox(
                            width: 26,
                            height: 26,
                            child: CircularProgressIndicator(
                              color: Colors.white,
                              strokeWidth: 3,
                            ),
                          )
                        else
                          const Text(
                            'SOS',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 29,
                              fontWeight: FontWeight.w900,
                              letterSpacing: 2,
                            ),
                          ),
                        const SizedBox(height: 4),
                        Text(
                          _c.busy ? 'Đang gửi' : 'Nhấn để gọi',
                          style: const TextStyle(
                            color: Colors.white70,
                            fontSize: 10,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildComposeCta() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 18, 16, 4),
      child: Material(
        color: _red,
        borderRadius: BorderRadius.circular(24),
        elevation: 3,
        child: InkWell(
          borderRadius: BorderRadius.circular(24),
          onTap: _c.busy ? null : _send,
          child: Padding(
            padding: const EdgeInsets.all(19),
            child: Row(
              children: [
                Container(
                  width: 54,
                  height: 54,
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: .18),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.add_a_photo_outlined,
                    color: Colors.white,
                    size: 28,
                  ),
                ),
                const SizedBox(width: 15),
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Gửi bài cứu hộ',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 19,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      SizedBox(height: 4),
                      Text(
                        'Ảnh hiện trường → AI phân tích → đội cứu hộ',
                        style: TextStyle(
                          color: Colors.white70,
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
                const Icon(
                  Icons.arrow_forward_ios,
                  color: Colors.white70,
                  size: 17,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildHomeContent() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (_c.pendingCount > 0) _buildPendingBanner(),
          if (_c.lastMessage != null) _buildMessage(),
          const Text(
            'SỐ KHẨN CẤP',
            style: TextStyle(
              color: Colors.black54,
              fontSize: 11,
              fontWeight: FontWeight.w900,
              letterSpacing: 1.4,
            ),
          ),
          const SizedBox(height: 10),
          Row(
            children: const [
              _EmergencyCard(
                number: '112',
                label: 'Cứu nạn',
                color: Color(0xFFE8EAF6),
              ),
              SizedBox(width: 8),
              _EmergencyCard(
                number: '114',
                label: 'Cứu hỏa',
                color: Color(0xFFFFF3E0),
              ),
              SizedBox(width: 8),
              _EmergencyCard(
                number: '115',
                label: 'Cấp cứu',
                color: Color(0xFFFFEBEE),
              ),
            ],
          ),
          const SizedBox(height: 20),
          const Text(
            'TRẠNG THÁI THIẾT BỊ',
            style: TextStyle(
              color: Colors.black54,
              fontSize: 11,
              fontWeight: FontWeight.w900,
              letterSpacing: 1.4,
            ),
          ),
          const SizedBox(height: 10),
          _statusRow(
            Icons.wifi,
            'Kết nối mạng',
            _c.netLabel,
            _c.netLabel != 'none',
          ),
          _statusRow(
            Icons.memory,
            'Mô hình AI offline',
            _c.modelReady ? 'Sẵn sàng' : 'Đang nạp',
            _c.modelReady,
          ),
          _statusRow(
            Icons.cloud_upload_outlined,
            'Hàng đợi đồng bộ',
            '${_c.pendingCount} bản ghi',
            _c.pendingCount == 0,
          ),
        ],
      ),
    );
  }

  Widget _buildPendingBanner() => _infoBanner(
    Icons.sync,
    '${_c.pendingCount} bản ghi đang chờ đồng bộ',
    'Đồng bộ ngay',
    _c.syncAll,
  );

  Widget _buildMessage() => Padding(
    padding: const EdgeInsets.only(bottom: 14),
    child: Text(
      _c.lastMessage!,
      style: const TextStyle(
        color: _red,
        fontSize: 12,
        fontWeight: FontWeight.w800,
      ),
    ),
  );

  Widget _infoBanner(
    IconData icon,
    String title,
    String action,
    VoidCallback onPressed,
  ) => Container(
    margin: const EdgeInsets.only(bottom: 18),
    padding: const EdgeInsets.all(12),
    decoration: BoxDecoration(
      color: Colors.orange.shade50,
      border: Border.all(color: Colors.orange.shade100),
      borderRadius: BorderRadius.circular(14),
    ),
    child: Row(
      children: [
        Icon(icon, color: Colors.orange.shade800, size: 18),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            title,
            style: TextStyle(
              color: Colors.orange.shade900,
              fontSize: 12,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
        TextButton(
          onPressed: onPressed,
          child: Text(
            action,
            style: TextStyle(
              color: Colors.orange.shade900,
              fontWeight: FontWeight.w900,
              fontSize: 11,
            ),
          ),
        ),
      ],
    ),
  );

  Widget _statusRow(IconData icon, String label, String value, bool good) =>
      Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 12),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: Colors.black.withValues(alpha: .05)),
        ),
        child: Row(
          children: [
            Icon(icon, color: _red, size: 19),
            const SizedBox(width: 11),
            Expanded(
              child: Text(
                label,
                style: const TextStyle(
                  color: Colors.black87,
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
            Text(
              value,
              style: TextStyle(
                color: good ? Colors.green.shade700 : Colors.orange.shade800,
                fontSize: 12,
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(width: 6),
            Icon(
              Icons.circle,
              color: good ? Colors.green : Colors.orange,
              size: 8,
            ),
          ],
        ),
      );

  Widget _buildHistory() {
    final records = _c.records;
    return Column(
      children: [
        _pageHeader('LỊCH SỬ', 'Bài cứu hộ'),
        Expanded(
          child: !_c.storeReady
              ? const Center(child: CircularProgressIndicator(color: _red))
              : records.isEmpty
              ? _emptyState(
                  Icons.description_outlined,
                  'Chưa có bài cứu hộ nào',
                )
              : ListView.separated(
                  padding: const EdgeInsets.all(16),
                  itemCount: records.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 10),
                  itemBuilder: (_, i) => _recordCard(records[i]),
                ),
        ),
      ],
    );
  }

  Widget _pageHeader(String eyebrow, String title) => Container(
    width: double.infinity,
    padding: const EdgeInsets.fromLTRB(20, 26, 20, 20),
    color: _red,
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          eyebrow,
          style: const TextStyle(
            color: Colors.white60,
            fontSize: 11,
            fontWeight: FontWeight.w800,
            letterSpacing: 1.5,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          title,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 25,
            fontWeight: FontWeight.w900,
          ),
        ),
      ],
    ),
  );

  Widget _recordCard(RescueRecord r) => Container(
    padding: const EdgeInsets.all(15),
    decoration: BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.circular(17),
      border: Border.all(color: Colors.black.withValues(alpha: .05)),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                r.label,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w900,
                ),
              ),
            ),
            _statusChip(r.status),
          ],
        ),
        const SizedBox(height: 8),
        Text(
          '${(r.confidence * 100).toStringAsFixed(0)}% tin cậy · ${_modeLabel(r.mode)}',
          style: const TextStyle(
            color: Colors.black54,
            fontSize: 12,
            fontWeight: FontWeight.w700,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          DateTime.fromMillisecondsSinceEpoch(
            r.createdAtMs,
          ).toLocal().toString().substring(0, 16),
          style: const TextStyle(color: Colors.black38, fontSize: 11),
        ),
        if (r.note.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Text(
              r.note,
              style: const TextStyle(fontSize: 12, color: Colors.black54),
            ),
          ),
      ],
    ),
  );

  Widget _statusChip(String status) {
    final pending = status == 'pending';
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: pending ? Colors.orange.shade50 : Colors.green.shade50,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        pending ? 'Đang chờ' : 'Đã gửi',
        style: TextStyle(
          color: pending ? Colors.orange.shade800 : Colors.green.shade800,
          fontSize: 11,
          fontWeight: FontWeight.w900,
        ),
      ),
    );
  }

  Widget _emptyState(IconData icon, String text) => Center(
    child: Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(icon, color: Colors.black12, size: 54),
        const SizedBox(height: 12),
        Text(
          text,
          style: const TextStyle(
            color: Colors.black38,
            fontWeight: FontWeight.w700,
          ),
        ),
      ],
    ),
  );

  Widget _buildGuide() => Column(
    children: [
      _pageHeader('KIẾN THỨC AN TOÀN', 'Hướng dẫn & Sơ cứu'),
      Container(
        color: Colors.white,
        child: Row(
          children: ['Dùng app', 'Sơ cứu', 'Số điện thoại']
              .map(
                (tab) => Expanded(
                  child: InkWell(
                    onTap: () => setState(() => _guideTab = tab),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      child: Column(
                        children: [
                          Text(
                            tab,
                            style: TextStyle(
                              color: _guideTab == tab ? _red : Colors.black38,
                              fontSize: 12,
                              fontWeight: FontWeight.w900,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Container(
                            height: 2,
                            color: _guideTab == tab ? _red : Colors.transparent,
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              )
              .toList(),
        ),
      ),
      Expanded(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: _guideContent(),
        ),
      ),
    ],
  );

  List<Widget> _guideContent() {
    if (_guideTab == 'Số điện thoại') return [_guideNumbers()];
    if (_guideTab == 'Sơ cứu')
      return [
        _guideTip(
          'Lũ lụt / Ngập nước',
          'Di chuyển lên cao, tránh xa dòng nước chảy xiết. Không lội qua nước nếu không biết độ sâu.',
          Icons.water,
        ),
        _guideTip(
          'Hỏa hoạn',
          'Gọi 114, bò sát sàn để tránh khói và không dùng thang máy.',
          Icons.local_fire_department,
        ),
        _guideTip(
          'Người bị thương',
          'Gọi 115, cầm máu bằng vải sạch và không di chuyển nạn nhân khi nghi gãy xương.',
          Icons.medical_services,
        ),
      ];
    return [
      for (final item in const [
        ('1', 'Mở ứng dụng', 'GPS tự động xác định vị trí của bạn.'),
        ('2', 'Nhấn SOS', 'Gửi vị trí đến đội cứu hộ trong một chạm.'),
        (
          '3',
          'Gửi bài cứu hộ',
          'Chụp ảnh hiện trường để AI phân tích và gắn nhãn.',
        ),
        (
          '4',
          'Mô tả tình huống',
          'Ghi số người, tình trạng và mốc vị trí gần nhất.',
        ),
      ])
        _step(item.$1, item.$2, item.$3),
      _guideTip(
        'Lưu ý quan trọng',
        'Nếu không thể dùng app, hãy gọi ngay 112 · 113 · 114 · 115.',
        Icons.warning_amber,
      ),
    ];
  }

  Widget _step(String n, String title, String text) => Container(
    margin: const EdgeInsets.only(bottom: 10),
    padding: const EdgeInsets.all(14),
    decoration: BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.circular(16),
    ),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        CircleAvatar(
          radius: 19,
          backgroundColor: _red,
          child: Text(
            n,
            style: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.w900,
            ),
          ),
        ),
        const SizedBox(width: 13),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: const TextStyle(fontWeight: FontWeight.w900)),
              const SizedBox(height: 4),
              Text(
                text,
                style: const TextStyle(
                  color: Colors.black54,
                  fontSize: 12,
                  height: 1.4,
                ),
              ),
            ],
          ),
        ),
      ],
    ),
  );

  Widget _guideTip(String title, String text, IconData icon) => Container(
    margin: const EdgeInsets.only(bottom: 10),
    padding: const EdgeInsets.all(15),
    decoration: BoxDecoration(
      color: const Color(0xFFFFF8F0),
      border: Border.all(color: Colors.orange.shade100),
      borderRadius: BorderRadius.circular(16),
    ),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, color: Colors.orange.shade800),
        const SizedBox(width: 11),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: TextStyle(
                  color: Colors.orange.shade900,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: 5),
              Text(
                text,
                style: const TextStyle(
                  color: Colors.black54,
                  fontSize: 12,
                  height: 1.4,
                ),
              ),
            ],
          ),
        ),
      ],
    ),
  );

  Widget _guideNumbers() => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: const [
      _EmergencyCard(
        number: '112',
        label: 'Tìm kiếm cứu nạn',
        color: Color(0xFFE8EAF6),
      ),
      SizedBox(height: 10),
      _EmergencyCard(number: '113', label: 'Công an', color: Color(0xFFE3F2FD)),
      SizedBox(height: 10),
      _EmergencyCard(number: '114', label: 'Cứu hỏa', color: Color(0xFFFFF3E0)),
      SizedBox(height: 10),
      _EmergencyCard(
        number: '115',
        label: 'Cấp cứu y tế',
        color: Color(0xFFFFEBEE),
      ),
    ],
  );

  Widget _buildNavigation() => NavigationBar(
    selectedIndex: _tab,
    onDestinationSelected: (i) => setState(() => _tab = i),
    backgroundColor: Colors.white,
    indicatorColor: const Color(0xFFFFCDD2),
    height: 72,
    destinations: const [
      NavigationDestination(
        icon: Icon(Icons.home_outlined),
        selectedIcon: Icon(Icons.home),
        label: 'Trang chủ',
      ),
      NavigationDestination(
        icon: Icon(Icons.description_outlined),
        selectedIcon: Icon(Icons.description),
        label: 'Lịch sử',
      ),
      NavigationDestination(
        icon: Icon(Icons.menu_book_outlined),
        selectedIcon: Icon(Icons.menu_book),
        label: 'Hướng dẫn',
      ),
    ],
  );

  String _modeLabel(SendMode mode) => switch (mode) {
    SendMode.fullImage => 'ẢNH GỐC',
    SendMode.compressedImage => 'ẢNH NÉN',
    SendMode.textOnly => 'CHỈ TEXT',
    SendMode.smsFallback => 'SMS',
    SendMode.queuedOffline => 'QUEUE',
  };
}

class _EmergencyCard extends StatelessWidget {
  const _EmergencyCard({
    required this.number,
    required this.label,
    required this.color,
  });
  final String number;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) => Expanded(
    child: Container(
      padding: const EdgeInsets.symmetric(vertical: 13, horizontal: 7),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(14),
      ),
      child: Column(
        children: [
          Text(
            number,
            style: const TextStyle(
              color: _red,
              fontSize: 20,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 3),
          Text(
            label,
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: Colors.black54,
              fontSize: 10,
              fontWeight: FontWeight.w800,
            ),
          ),
        ],
      ),
    ),
  );
}
