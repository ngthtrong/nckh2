import '../../domain/entities/emergency_number.dart';
import '../../domain/entities/first_aid_item.dart';
import '../../domain/entities/region.dart';

class EmergencyData {
  static const List<({String number, String label})> quickNumbers = [
    (number: '114', label: 'Cứu hỏa'),
    (number: '115', label: 'Cấp cứu'),
    (number: '113', label: 'Công an'),
  ];

  static const List<Region> regions = [
    Region(
      label: 'Toàn quốc',
      numbers: [
        EmergencyNumber(name: 'Cứu hỏa', num: '114', colorType: 'orange'),
        EmergencyNumber(name: 'Cấp cứu y tế', num: '115', colorType: 'red'),
        EmergencyNumber(name: 'Công an', num: '113', colorType: 'blue'),
        EmergencyNumber(name: 'Tìm kiếm cứu nạn', num: '112', colorType: 'purple'),
      ],
      guides: [],
    ),
    Region(
      label: 'TP.HCM',
      numbers: [
        EmergencyNumber(name: 'PCCC TP.HCM', num: '028 3864 3456', colorType: 'orange'),
        EmergencyNumber(name: 'BV Chợ Rẫy', num: '028 3855 4137', colorType: 'red'),
        EmergencyNumber(name: 'Cảnh sát 113', num: '028 3839 0411', colorType: 'blue'),
        EmergencyNumber(name: 'Cứu hộ giao thông', num: '028 3812 3456', colorType: 'green'),
      ],
      guides: [
        'Lũ lụt khu vực thấp: Quận 8, Bình Thạnh, Thủ Đức',
        'Sạt lở: khu vực ven sông Sài Gòn, Nhà Bè',
      ],
    ),
    Region(
      label: 'Hà Nội',
      numbers: [
        EmergencyNumber(name: 'PCCC Hà Nội', num: '024 3856 3456', colorType: 'orange'),
        EmergencyNumber(name: 'BV Bạch Mai', num: '024 3869 3731', colorType: 'red'),
        EmergencyNumber(name: 'Cảnh sát 113', num: '024 3942 3456', colorType: 'blue'),
        EmergencyNumber(name: 'Tìm kiếm cứu nạn', num: '024 3733 0686', colorType: 'purple'),
      ],
      guides: [
        'Ngập lụt: Hà Đông, Long Biên, Hoàng Mai sau mưa lớn',
        'Sạt lở đê: khu vực ven sông Hồng, Ba Vì',
      ],
    ),
    Region(
      label: 'Miền Trung',
      numbers: [
        EmergencyNumber(name: 'PCCC Đà Nẵng', num: '0236 3823 456', colorType: 'orange'),
        EmergencyNumber(name: 'BV Đà Nẵng', num: '0236 3821 480', colorType: 'red'),
        EmergencyNumber(name: 'PCCC Huế', num: '0234 3823 456', colorType: 'orange'),
        EmergencyNumber(name: 'Ủy ban PCTT TW', num: '024 3733 0797', colorType: 'purple'),
      ],
      guides: [
        'Bão & lũ: Quảng Nam, Quảng Ngãi, Bình Định tháng 9–12',
        'Sạt lở núi: Tây Nguyên, Quảng Trị mùa mưa',
      ],
    ),
    Region(
      label: 'Đồng bằng SCL',
      numbers: [
        EmergencyNumber(name: 'PCCC Cần Thơ', num: '0292 3812 114', colorType: 'orange'),
        EmergencyNumber(name: 'BV Cần Thơ', num: '0292 3822 895', colorType: 'red'),
        EmergencyNumber(name: 'Cứu hộ đường thủy', num: '0292 3813 456', colorType: 'teal'),
        EmergencyNumber(name: 'Ủy ban PCTT vùng', num: '0292 3820 797', colorType: 'purple'),
      ],
      guides: [
        'Lũ mùa nước nổi: An Giang, Đồng Tháp tháng 8–11',
        'Sạt lở bờ sông: Vĩnh Long, Tiền Giang, Bến Tre',
      ],
    ),
  ];

  static const List<FirstAidItem> firstAidItems = [
    FirstAidItem(
      title: 'Lũ lụt / Ngập nước',
      type: 'blue',
      icon: '🌊',
      steps: [
        'Di chuyển ngay lên cao, tránh xa dòng nước chảy xiết',
        'Không lội qua nước ngập nếu không biết độ sâu',
        'Tắt điện, gas trước khi rời khỏi nhà',
        'Mang theo giấy tờ tùy thân trong túi chống nước',
      ],
    ),
    FirstAidItem(
      title: 'Hỏa hoạn',
      type: 'orange',
      icon: '🔥',
      steps: [
        'Gọi 114 ngay lập tức, không cố dập lửa lớn',
        'Bò sát sàn để tránh khói — khói độc nặng hơn không khí',
        'Bịt kín khe cửa bằng vải ẩm nếu không thoát được',
        'Không dùng thang máy, chỉ dùng cầu thang bộ',
      ],
    ),
    FirstAidItem(
      title: 'Người bị thương',
      type: 'red',
      icon: '🩹',
      steps: [
        'Gọi 115 trước, đừng di chuyển nạn nhân nếu có thể gãy xương',
        'Ép chặt vết thương để cầm máu bằng vải sạch',
        'Giữ nạn nhân tỉnh táo, nói chuyện liên tục',
        'Nếu ngưng thở: ép tim 30 lần, thổi ngạt 2 lần',
      ],
    ),
    FirstAidItem(
      title: 'Sạt lở / Sập nhà',
      type: 'yellow',
      icon: '🏚️',
      steps: [
        'Di tản ngay khỏi khu vực nguy hiểm, không quay lại',
        'Nếu mắc kẹt: gõ vào tường/ống để báo hiệu',
        'Che miệng, mũi để tránh bụi',
        'Đừng thắp nến hoặc bật lửa — có thể có rò rỉ khí gas',
      ],
    ),
  ];

  static const List<({String number, String title, String desc})> appSteps = [
    (number: '1', title: 'Mở ứng dụng', desc: 'Mở ứng dụng ngay khi gặp tình huống khẩn cấp. GPS tự động xác định vị trí.'),
    (number: '2', title: 'Nhấn SOS (nếu nguy cấp)', desc: 'Nút SOS lớn ở trang chủ — gửi vị trí đến đội cứu hộ trong 1 chạm.'),
    (number: '3', title: 'Gửi bài cứu hộ', desc: 'Chụp ảnh hiện trường — AI tự gắn thẻ loại tai nạn. Thêm mô tả rồi nhấn Gửi.'),
    (number: '4', title: 'Mô tả tình huống', desc: 'Ghi rõ: số người mắc kẹt, số người bị thương, đối tượng ưu tiên.'),
    (number: '5', title: 'Chờ phản hồi', desc: 'Đội cứu hộ sẽ xác nhận qua thông báo. Giữ điện thoại có pin và sóng.'),
  ];
}
