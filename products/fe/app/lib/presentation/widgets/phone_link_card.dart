import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../domain/entities/emergency_number.dart';

class PhoneLinkCard extends StatelessWidget {
  final EmergencyNumber item;
  final bool compact;

  const PhoneLinkCard({
    super.key,
    required this.item,
    this.compact = false,
  });

  Color _getBgColor() {
    switch (item.colorType) {
      case 'red':
        return const Color(0xFFFEF2F2);
      case 'orange':
        return const Color(0xFFFFF7ED);
      case 'blue':
        return const Color(0xFFEFF6FF);
      case 'green':
        return const Color(0xFFF0FDF4);
      case 'teal':
        return const Color(0xFFF0FDFA);
      case 'purple':
      default:
        return const Color(0xFFFAF5FF);
    }
  }

  Color _getTextColor() {
    switch (item.colorType) {
      case 'red':
        return const Color(0xFFB91C1C);
      case 'orange':
        return const Color(0xFFC2410C);
      case 'blue':
        return const Color(0xFF1D4ED8);
      case 'green':
        return const Color(0xFF15803D);
      case 'teal':
        return const Color(0xFF0F766E);
      case 'purple':
      default:
        return const Color(0xFF7E22CE);
    }
  }

  Color _getBorderColor() {
    switch (item.colorType) {
      case 'red':
        return const Color(0xFFFCA5A5);
      case 'orange':
        return const Color(0xFFFDBA74);
      case 'blue':
        return const Color(0xFF93C5FD);
      case 'green':
        return const Color(0xFF86EFAC);
      case 'teal':
        return const Color(0xFF99F6E4);
      case 'purple':
      default:
        return const Color(0xFFD8B4FE);
    }
  }

  Future<void> _makeCall() async {
    final Uri uri = Uri.parse('tel:${item.num.replaceAll(' ', '')}');
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Material(
      color: _getBgColor(),
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        onTap: _makeCall,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: EdgeInsets.symmetric(
            horizontal: 14,
            vertical: compact ? 10 : 14,
          ),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: _getBorderColor()),
          ),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      item.name,
                      style: TextStyle(
                        color: _getTextColor(),
                        fontSize: compact ? 12 : 13,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      item.num,
                      style: TextStyle(
                        color: _getTextColor(),
                        fontSize: compact ? 14 : 16,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ],
                ),
              ),
              Icon(Icons.phone, color: _getTextColor(), size: 20),
            ],
          ),
        ),
      ),
    );
  }
}
