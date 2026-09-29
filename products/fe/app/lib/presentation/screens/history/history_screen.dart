import 'dart:async';

import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../controllers/app_controller.dart';
import '../../../domain/entities/rescue_record.dart';
import '../../widgets/post_card.dart';

class HistoryScreen extends StatefulWidget {
  final AppController controller;
  final bool active;

  const HistoryScreen({super.key, required this.controller, this.active = false});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  static const _pageSize = 5;
  final _scrollController = ScrollController();
  final _records = <RescueRecord>[];
  bool _loading = false;
  bool _hasMore = true;

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
    widget.controller.addListener(_onControllerChanged);
    if (widget.active) unawaited(_reload());
  }

  @override
  void didUpdateWidget(covariant HistoryScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.controller != widget.controller) {
      oldWidget.controller.removeListener(_onControllerChanged);
      widget.controller.addListener(_onControllerChanged);
    }
    if (widget.active && !oldWidget.active) unawaited(_reload());
  }

  @override
  void dispose() {
    widget.controller.removeListener(_onControllerChanged);
    _scrollController
      ..removeListener(_onScroll)
      ..dispose();
    super.dispose();
  }

  Future<void> _reload() async {
    if (_loading) return;
    setState(() {
      _records.clear();
      _hasMore = true;
    });
    if (_scrollController.hasClients) _scrollController.jumpTo(0);
    await _loadNextPage();
  }

  /// Trạng thái điều phối mới, bản ghi vừa đồng bộ/bị từ chối: đọc lại các trang đã
  /// hiển thị (giữ vị trí cuộn) để thẻ bài cập nhật mà không cần mở lại tab.
  void _onControllerChanged() {
    if (!mounted || !widget.active || _loading || _records.isEmpty) return;
    final fresh = widget.controller.getRecordsPage(
      offset: 0,
      limit: _records.length,
    );
    final count = widget.controller.recordCount;
    setState(() {
      _records
        ..clear()
        ..addAll(fresh);
      _hasMore = _records.length < count;
    });
  }

  void _onScroll() {
    if (_scrollController.hasClients &&
        _scrollController.position.extentAfter < 160) {
      unawaited(_loadNextPage());
    }
  }

  Future<void> _loadNextPage() async {
    if (!widget.active || _loading || !_hasMore) return;
    setState(() => _loading = true);
    await Future<void>.delayed(Duration.zero);
    if (!mounted || !widget.active) {
      if (mounted) setState(() => _loading = false);
      return;
    }
    final page = widget.controller.getRecordsPage(
      offset: _records.length,
      limit: _pageSize,
    );
    final count = widget.controller.recordCount;
    if (!mounted) return;
    setState(() {
      _records.addAll(page);
      _hasMore = _records.length < count;
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: double.infinity,
          padding: const EdgeInsets.fromLTRB(20, 24, 20, 18),
          color: AppColors.primaryRed,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: const [
              Text(
                'LỊCH SỬ',
                style: TextStyle(
                  color: Colors.white60,
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 1.5,
                ),
              ),
              SizedBox(height: 3),
              Text(
                'Bài cứu hộ',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 24,
                  fontWeight: FontWeight.w900,
                ),
              ),
            ],
          ),
        ),
        Expanded(
          child: _records.isEmpty && _loading
              ? const Center(child: CircularProgressIndicator())
              : _records.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Container(
                            width: 64,
                            height: 64,
                            decoration: const BoxDecoration(
                              color: Color(0xFFF3F4F6),
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(
                              Icons.history_outlined,
                              color: Color(0xFF9CA3AF),
                              size: 32,
                            ),
                          ),
                          const SizedBox(height: 12),
                          const Text(
                            'Chưa có bài cứu hộ nào',
                            style: TextStyle(
                              color: Color(0xFF9CA3AF),
                              fontWeight: FontWeight.w600,
                              fontSize: 14,
                            ),
                          ),
                        ],
                      ),
                    )
                  : ListView.builder(
                      controller: _scrollController,
                      padding: const EdgeInsets.all(16),
                      physics: const BouncingScrollPhysics(
                        parent: AlwaysScrollableScrollPhysics(),
                      ),
                      itemCount: _records.length + (_hasMore ? 1 : 0),
                      itemBuilder: (context, index) {
                        if (index == _records.length) {
                          return Padding(
                            padding: const EdgeInsets.all(16),
                            child: Center(
                              child: _loading
                                  ? const CircularProgressIndicator()
                                  : const Text('Cuộn để tải thêm'),
                            ),
                          );
                        }
                        return PostCard(record: _records[index]);
                      },
                    ),
        ),
      ],
    );
  }
}
