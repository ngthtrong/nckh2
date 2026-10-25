"""Author reviewed copies only. Source diagrams and report inputs are read-only."""
from pathlib import Path
import copy
import hashlib
import heapq
import html
import json
import math
import textwrap
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parents[1]
PAGES = {}
BLUE = '#EDF3FA'
STROKE = '#526B88'


class Page:
    def __init__(self, name, title, note=''):
        self.name, self.title, self.note = name, title, note
        self.nodes, self.edges, self.lanes = {}, [], []

    def n(self, key, text, col, row, kind='process', width=300, height=None):
        height = height or (120 if kind == 'decision' else 100)
        if kind == 'decision':
            text='\n'.join(textwrap.fill(line,22,break_long_words=False) for line in text.splitlines())
        self.nodes[key] = dict(text=text, x=70 + col * 380, y=125 + row * 170,
                               w=width, h=height, kind=kind)
        return self

    def xy(self, key, text, x, y, kind='process', width=290, height=76, lane=None):
        self.nodes[key] = dict(text=text, x=x, y=y, w=width, h=height, kind=kind, lane=lane)
        return self

    def e(self, source, target, label='', dashed=False):
        self.edges.append((source, target, label, dashed))
        return self

    def chain(self, *keys):
        for a, b in zip(keys, keys[1:]):
            self.e(a, b)
        return self


def add(stem, *pages):
    PAGES[stem] = list(pages)


# Overview: separate asynchronous channels, software work, and field work.
p = Page('Tổng quan bốn phân hệ', 'LUỒNG PHỐI HỢP TỔNG THỂ',
         'Hình tổng quan. Các ô quy trình con được mô tả trong flow_01 đến flow_08. '
         'Phản hồi HTTP xác nhận tiếp nhận thông tin; SMS không tạo ACK HTTP trực tiếp cho app.')
for i, title in enumerate(['ỨNG DỤNG DI ĐỘNG BIÊN', 'TIẾP NHẬN VÀ LƯU TRỮ', 'PHÂN CỤM VÀ ƯU TIÊN', 'ĐIỀU PHỐI WEB']):
    p.lanes.append((f'lane{i}', title, 40+i*430, 105, 410, 1540))
for key,text,col,y,kind in [
 ('start','Người dùng mở ứng dụng',0,170,'start'),
 ('request','Tạo SOS hoặc báo cáo chi tiết\nẢnh và AI là tùy chọn',0,310,'subprocess'),
 ('local','Lưu yêu cầu trên thiết bị\nXếp hàng để gửi',0,450,'process'),
 ('send','Đồng bộ qua Internet\nThử SMS dự phòng khi đủ điều kiện',0,590,'subprocess'),
 ('local_result','Cập nhật kết quả gửi\nGiữ phần chưa gửi để thử lại',0,1030,'process'),
 ('track','Theo dõi gửi và trạng thái\nĐồng bộ lại khi có mạng',0,1210,'subprocess'),
 ('closed','Yêu cầu đã kết thúc?',0,1360,'decision'),
 ('end','Kết thúc theo dõi yêu cầu',0,1540,'end'),
 ('receive','Tiếp nhận qua HTTP\nhoặc SMS Gateway',1,590,'process'),
 ('validate','Kiểm tra và chống trùng\ntheo từng kênh tiếp nhận',1,740,'subprocess'),
 ('save','Lưu hoặc bổ sung báo cáo\nCập nhật phiên bản dữ liệu',1,890,'process'),
 ('http','Trả kết quả cho bên gửi HTTP',1,1030,'process'),
 ('audit','Lưu thay đổi điều phối\nvà nhật ký thao tác',1,1380,'process'),
 ('cache','Lấy kết quả từ bộ nhớ đệm\nTính lại khi dữ liệu thay đổi',2,450,'subprocess'),
 ('cluster','Tách báo cáo cần xác minh\nPhân cụm và tính ưu tiên',2,650,'subprocess'),
 ('snapshot','Cung cấp cụm ưu tiên\nvà hàng cần xác minh',2,890,'process'),
 ('login','Điều phối viên đăng nhập',3,170,'start'),
 ('poll','Lấy cập nhật định kỳ',3,450,'process'),
 ('view','Xem bản đồ và cụm ưu tiên\nXác minh ca thiếu thông tin',3,890,'process'),
 ('assign','Chọn ca và giao đội phụ trách',3,1060,'process'),
 ('dispatch','Cập nhật trạng thái\n“Đã điều phối”',3,1210,'process'),
 ('field','Cứu hộ ngoài thực địa\nĐiều phối viên cập nhật kết quả',3,1380,'external'),
 ('close','Đã giải quyết hoặc đã đóng ca',3,1530,'end'),
]:
    p.xy(key,text,100+430*col,y,kind,height=110 if kind=='decision' else (76 if kind in ('start','end') else 100),lane=f'lane{col}')
p.chain('start','request','local','send').e('send','receive','HTTP / Gateway')
p.chain('receive','validate','save','http').e('http','local_result','Kết quả HTTP')
p.chain('local_result','track','closed').e('closed','end','Đã kết thúc').e('closed','track','Chưa')
p.e('send','local_result','Kết quả SMS / chờ gửi',True)
p.chain('login','poll').e('poll','cache','Yêu cầu kết quả')
# This edge is a dependency, not a claim that every read recomputes the graph.
p.e('cache','cluster','Khi cần cập nhật',True).e('cache','snapshot','Kết quả đang có')
p.e('cluster','snapshot','Kết quả mới').e('snapshot','view','Cụm và hàng xác minh')
p.chain('view','assign','dispatch','field','close')
p.e('dispatch','audit','Đổi trạng thái',True).e('field','audit','Ghi nhận kết quả',True)
p.e('save','cache','Dữ liệu đổi',True).e('audit','cache','Trạng thái / vị trí đổi',True)
add('flowchart',p)

p=Page('SOS một chạm','GỬI YÊU CẦU SOS',
       'SOS không ảnh không đo /probe và không tự gán urgency = 1.0. '
       'Thất bại ở GPS hoặc truyền dữ liệu không làm mất yêu cầu đã lưu.')
p.n('start','Nhấn SOS một chạm',1,0,'start').n('recent','Có SOS vừa tạo\ntrong 30 giây?',1,1,'decision')
p.n('reuse','Dùng lại SOS gần nhất\nGửi lại khi đủ điều kiện',0,2,'subprocess')
p.n('create','Tạo SOS và lưu ngay\ntrên thiết bị',1,2)
p.n('gps','Thử lấy vị trí trong thời gian giới hạn',1,3).n('location','Có vị trí?',1,4,'decision')
p.n('has','Bổ sung tọa độ và sai số',2,5).n('missing','Giữ vị trí trống\nTrung tâm xác minh sau',0,5)
p.n('deliver','Gửi thông tin qua Internet\nSMS dự phòng khi đủ điều kiện',1,6,'subprocess')
p.n('result','Hiển thị kết quả gửi thực tế\nGiữ yêu cầu nếu chưa gửi xong',1,7).n('end','Hoàn tất thao tác SOS',1,8,'end')
p.chain('start','recent').e('recent','reuse','Có').e('recent','create','Không')
p.chain('create','gps','location').e('location','has','Có').e('location','missing','Không')
p.e('has','deliver').e('missing','deliver').e('reuse','deliver','Khi cần gửi lại')
p.chain('deliver','result','end');add('flow_01_sos_one_touch',p)
p.e('reuse','result','Không cần gửi lại')

p=Page('Tạo báo cáo','TẠO BÁO CÁO CỨU HỘ VÀ NHẬN DIỆN ẢNH',
       'Không có ảnh hoặc AI không khả dụng: giữ nhãn AI trống, không gán non_flood. '
       'Điểm khẩn cấp trên app không được giả định là đầu vào E mà adapter backend đã sử dụng.')
p.n('start','Mở biểu mẫu báo cáo',1,0,'start').n('input','Nhập tình trạng và số người\nChọn nhóm yếu thế',1,1)
p.n('photo','Có ảnh và AI khả dụng?',1,2,'decision')
p.n('ai','Nhận diện mức ngập từ ảnh\nLưu nhãn và độ tin cậy',0,3,'subprocess')
p.n('skip','Bỏ qua nhận diện\nGiữ nhãn AI trống',2,3)
p.n('submit','Người dùng chọn gửi báo cáo',1,4).n('gps','Thử lấy vị trí\nGiữ trống nếu không lấy được',1,5)
p.n('urgency','Tính điểm khẩn cấp\nnếu mô hình sẵn sàng',1,6)
p.n('valid','Thông tin và ảnh lưu được?',1,7,'decision')
p.n('error','Thông báo lỗi để người dùng sửa\nChưa tạo báo cáo mới',2,8)
p.n('save','Lưu báo cáo và ảnh trên thiết bị',1,8)
p.n('deliver','Chuyển sang quy trình gửi\nvà lưu hàng đợi',1,9,'subprocess').n('end','Hiển thị kết quả gửi',1,10,'end')
p.chain('start','input','photo').e('photo','ai','Có').e('photo','skip','Không')
p.e('ai','submit').e('skip','submit').chain('submit','gps','urgency','valid')
p.e('valid','error','Không').e('error','input','Sửa thông tin').e('valid','save','Có').chain('save','deliver','end')
add('flow_02_create_report_edge_ai',p)

send=Page('Lưu và gửi yêu cầu','GỬI THÍCH ỨNG: THÔNG TIN ĐI TRƯỚC, ẢNH ĐI SAU',
          'accepted / duplicate là ACK của metadata. synced chỉ hoàn tất khi đã xử lý xong phần ảnh theo chế độ gửi. '
          'Worker đồng bộ nền không tự gửi SMS; SMS được thử trong luồng thao tác của người dùng khi đủ điều kiện.')
send.n('start','Yêu cầu đã lưu trên thiết bị',1,0,'start').n('policy','Chọn chế độ gửi\nXem trang Chính sách mạng',1,1,'subprocess')
send.n('queue','Lưu bản ghi và xếp hàng message',1,2).n('sms_mode','Đang chọn SMS dự phòng?',1,3,'decision')
send.n('http','Gửi metadata qua /sync/messages',1,4).n('ack','Kết quả gửi metadata?',1,5,'decision')
send.n('accepted','Ghi nhận metadata đã được nhận\nXóa message đã ACK khỏi hàng đợi',0,6)
send.n('retry','Giữ hàng đợi\nĐặt lịch thử lại có giãn cách',1,6)
send.n('rejected','Phục hồi lỗi được phép\nhoặc ghi lỗi không thể gửi',2,6,'subprocess')
send.n('attachment','Hoàn tất phần ảnh\nXem trang Xử lý ảnh',0,7,'subprocess')
send.n('sms','Thử SMS nếu đủ điều kiện\nGiữ bản ghi chờ đồng bộ data',1,8,'subprocess')
send.n('result','Hiển thị kết quả thực tế\nGiữ phần còn chờ để thử lại',1,9).n('end','Kết thúc lượt gửi',1,10,'end')
send.chain('start','policy','queue','sms_mode').e('sms_mode','sms','Có').e('sms_mode','http','Không')
send.chain('http','ack').e('ack','accepted','Đã nhận / trùng').e('ack','retry','Lỗi tạm thời').e('ack','rejected','Bị từ chối')
send.chain('accepted','attachment','result').chain('retry','sms','result').e('rejected','result').e('result','end')
image=Page('Xử lý ảnh','HOÀN TẤT PHẦN ẢNH SAU KHI METADATA ĐÃ ĐƯỢC NHẬN',
           'Nếu ảnh gửi lỗi: metadata vẫn có thể đã tới máy chủ. Giữ trạng thái chờ ảnh, không gửi lại metadata đã ACK. '
           'Ảnh định dạng không được máy chủ hỗ trợ có thể được chuyển sang JPEG trước khi tải lên.')
image.n('start','Metadata đã được xác nhận',1,0,'start').n('needed','Cần gửi ảnh?',1,1,'decision')
image.n('done','Đánh dấu đồng bộ hoàn tất',0,5).n('compress','Nén ảnh hoặc giữ ảnh gốc\ntheo chế độ đã chọn',1,2,'subprocess')
image.n('upload','Tải ảnh qua /api/reports',1,3).n('ok','Ảnh gửi thành công?',1,4,'decision')
image.n('pending','Giữ phần ảnh chờ gửi\nThử lại khi có điều kiện',2,5).n('end','Trả kết quả đồng bộ',1,6,'end')
image.chain('start','needed').e('needed','done','Không ảnh / chỉ thông tin').e('needed','compress','Có')
image.chain('compress','upload','ok').e('ok','done','Có').e('ok','pending','Không').e('done','end').e('pending','end')
policy=Page('Chính sách mạng','CHỌN CHẾ ĐỘ GỬI THEO KẾT NỐI VÀ ĐỘ TIN CẬY AI',
            'Ngưỡng hiện tại: mạng mạnh ≥ 1.000 kbit/s; gửi ảnh nén từ 50 kbit/s; tin cậy AI cao ≥ 0,90. '
            'Ảnh nén: cạnh tối đa 1.024 px, chất lượng JPEG 60. SOS không ảnh bỏ qua phép đo thông lượng.')
policy.n('start','Đánh giá điều kiện gửi',1,0,'start').n('data','Có kết nối dữ liệu?',1,1,'decision')
policy.n('sms','Chọn SMS dự phòng',0,2).n('photo','Yêu cầu có ảnh?',1,2,'decision')
policy.n('probe','Đo thông lượng tới máy chủ\n/probe, tối đa 6 giây',1,3)
policy.n('throughput','Đo được thông lượng?',1,4,'decision').n('strong','Mạng mạnh?',1,5,'decision')
policy.n('conf','AI có độ tin cậy cao?',2,6,'decision').n('medium','Đủ băng thông gửi ảnh nén?',1,6,'decision')
policy.n('text','Chỉ gửi thông tin',0,7).n('compressed','Thông tin và ảnh nén',1,7).n('original','Thông tin và ảnh gốc',2,7)
policy.n('end','Trả chế độ gửi đã chọn',1,8,'end')
policy.chain('start','data').e('data','sms','Không').e('data','photo','Có').e('photo','text','Không')
policy.e('photo','probe','Có').chain('probe','throughput').e('throughput','sms','Không').e('throughput','strong','Có')
policy.e('strong','conf','≥ 1.000 kbit/s').e('strong','medium','< 1.000 kbit/s')
policy.e('medium','compressed','≥ 50 kbit/s').e('medium','text','< 50 kbit/s')
policy.e('conf','text','≥ 0,90').e('conf','original','< 0,90')
for n in ['sms','text','compressed','original']:policy.e(n,'end')
add('flow_03_adaptive_network_send',send,image,policy)

p=Page('Theo dõi trạng thái','TRA CỨU VÀ CẬP NHẬT TRẠNG THÁI CỨU HỘ',
       'API hiện trả ID, trạng thái và phiên bản; không trả vị trí đội, liên hệ đội hoặc lý do đóng cho app. '
       'Khi theo dõi: 15 giây; ngoài màn hình theo dõi: 60 giây. Dừng lịch khi app ra nền hoặc mất kết nối.')
p.n('start','Mở lịch sử hoặc theo dõi yêu cầu',1,0,'start').n('local','Hiển thị trạng thái đã lưu',1,1)
p.n('active','Còn yêu cầu cần theo dõi?',1,2,'decision').n('online','App đang hoạt động\nvà có kết nối?',1,3,'decision')
p.n('wait','Giữ trạng thái cục bộ\nChờ mở app hoặc có mạng',0,4)
p.n('fetch','Lấy trạng thái từ máy chủ\n/api/reports/status',1,4)
p.n('advanced','Nhận được trạng thái tiến?',1,5,'decision')
p.n('update','Lưu trạng thái mới trên thiết bị',1,6)
p.n('show','Hiển thị tiến trình xử lý',1,7).n('closed','Yêu cầu đã kết thúc?',1,8,'decision')
p.n('schedule','Hẹn lần tra cứu tiếp theo',0,9).n('end','Kết thúc theo dõi yêu cầu',1,10,'end')
p.chain('start','local','active').e('active','end','Không').e('active','online','Có')
p.e('online','wait','Không').e('wait','online','Khi có điều kiện').e('online','fetch','Có')
p.chain('fetch','advanced').e('advanced','update','Có').e('advanced','show','Không / lỗi mạng')
p.chain('update','show','closed').e('closed','end','Đã giải quyết / đã đóng').e('closed','schedule','Chưa')
p.e('schedule','online','Đến lịch');add('flow_04_track_rescue_status',p)

sync=Page('Đồng bộ message','BACKEND: TIẾP NHẬN BATCH VÀ CHỐNG TRÙNG MESSAGE',
          'POST /sync/messages: header hợp đồng phiên bản 1; tối đa 50 message, tổng 256 KiB. '
          'Quá dung lượng trả HTTP 413. ID/hash hoặc sequence xung đột trả rejected trong kết quả từng message; HTTP batch vẫn có thể là 200.')
sync.n('start','Nhận batch /sync/messages',1,0,'start').n('request','Kiểm tra phiên bản và giới hạn\nĐọc JSON hợp lệ',1,1,'subprocess')
sync.n('valid','Request hợp lệ?',1,2,'decision').n('bad','Trả lỗi request phù hợp\n400 hoặc 413',2,3)
sync.n('message','Xử lý từng message\ntrong giao dịch độc lập',1,3)
sync.n('verify','Kiểm tra cấu trúc, hash và hạn dùng',1,4,'subprocess')
sync.n('dup','Trùng message_id?',1,5,'decision').n('hash','Hash có khớp?',0,6,'decision')
sync.n('duplicate','Trả duplicate\nkèm kết quả đã lưu',0,7)
sync.n('sequence','Sequence có bị dùng lại?',1,6,'decision').n('reject','Trả rejected và mã lỗi\nKhông áp dụng thao tác',2,7)
sync.n('apply','Kiểm tra quyền và áp dụng thao tác\nLưu báo cáo hoặc đổi trạng thái',1,7,'subprocess')
sync.n('commit','Lưu dấu chống trùng và nhật ký\nCommit; trả accepted',1,8)
sync.n('results','Tổng hợp kết quả từng message\nLỗi bất ngờ: rollback và retry_later',1,9)
sync.n('end','Trả kết quả batch',1,10,'end')
sync.chain('start','request','valid').e('valid','bad','Không').e('valid','message','Có').chain('message','verify','dup')
sync.e('verify','reject','Dữ liệu / hash / hạn sai').e('dup','hash','Có').e('dup','sequence','Không')
sync.e('hash','duplicate','Khớp').e('hash','reject','Khác').e('sequence','reject','Có').e('sequence','apply','Không')
sync.chain('apply','commit','results','end').e('apply','reject','Không hợp lệ').e('duplicate','results').e('reject','results').e('bad','end')
multipart=Page('Tiếp nhận ảnh','BACKEND: TIẾP NHẬN ẢNH VÀ GỘP THEO ID BÁO CÁO',
               'Multipart dùng ID báo cáo để gộp; không đi qua message_id/sequence của batch. '
               'Giữ ảnh đầu tiên, chỉ bổ sung phần còn thiếu. Giới hạn hiện tại: metadata 64 KiB, ảnh 15 MB.')
multipart.n('start','Nhận /api/reports',1,0,'start').n('validate','Kiểm tra phiên bản, metadata\nvà quyền sở hữu báo cáo',1,1,'subprocess')
multipart.n('image','Có ảnh đính kèm?',1,2,'decision').n('check_image','Kiểm tra dung lượng, định dạng\nvà hash ảnh',1,3,'subprocess')
multipart.n('file','Lưu ảnh hợp lệ nếu cần',1,4).n('merge','Tạo hoặc bổ sung báo cáo\nGiữ dữ liệu và ảnh đã có',1,5)
multipart.n('save','Lưu nhật ký và phiên bản dữ liệu',1,6).n('end','Trả HTTP 201 và kết quả',1,7,'end')
multipart.n('error','Trả lỗi phù hợp\nKhông chấp nhận dữ liệu sai',2,4,'end')
multipart.chain('start','validate','image').e('validate','error','Không hợp lệ').e('image','check_image','Có')
multipart.e('image','merge','Không').chain('check_image','file','merge','save','end').e('check_image','error','Không hợp lệ')
sms=Page('Tiếp nhận SMS','BACKEND: TIẾP NHẬN SMS DO GATEWAY CHUYỂN TIẾP',
         'Gateway xác thực bằng token riêng; không bắt buộc header hợp đồng của batch. '
         'Phản hồi HTTP được gửi cho Gateway, không phải ACK trực tiếp tới điện thoại đã gửi SMS.')
sms.n('start','Gateway gọi /api/sms/inbound',1,0,'start').n('auth','Gateway được bật\nvà token hợp lệ?',1,1,'decision')
sms.n('deny','Từ chối Gateway\nHTTP 401 hoặc 403',2,2,'end').n('parse','Đọc người gửi và nội dung SMS',1,2)
sms.n('structured','SMS theo định dạng SOS?',1,3,'decision')
sms.n('same','Dùng ID trong tin SOS\nđể tạo hoặc gộp báo cáo',0,4).n('free','Tạo báo cáo từ tin tự do',2,4)
sms.n('save','Lưu báo cáo nguồn SMS\nGhi nhận thông tin liên hệ',1,5)
sms.n('end','Trả kết quả cho Gateway\n201 nếu mới, 200 nếu đã có',1,6,'end')
sms.chain('start','auth').e('auth','deny','Không').e('auth','parse','Có').chain('parse','structured')
sms.e('structured','same','Có').e('structured','free','Không').e('same','save').e('free','save').e('save','end')
add('flow_05_backend_ingest_dedup',sync,multipart,sms)

cache=Page('Cấp kết quả phân cụm','CUNG CẤP KẾT QUẢ PHÂN CỤM QUA BỘ NHỚ ĐỆM',
           'ETag thuộc snapshot đã tính, không phải trực tiếp phiên bản dữ liệu hiện tại. '
           'Có thể trả snapshot cũ khi đang tính nền; computedAt và stale giúp diễn giải kết quả.')
cache.n('start','Dashboard gọi /api/clusters',1,0,'start').n('snapshot','Lấy snapshot qua dịch vụ bộ nhớ đệm',1,1,'subprocess')
cache.n('current','Đã có snapshot\nkhớp phiên bản dữ liệu?',1,2,'decision')
cache.n('refresh','Tính ngay hoặc lên lịch tính nền\ntheo thời gian tính và giới hạn tần suất',2,3,'subprocess')
cache.n('available','Dùng snapshot sẵn có\nhoặc snapshot vừa tính',1,4)
cache.n('etag','If-None-Match khớp\nETag snapshot trả về?',1,5,'decision')
cache.n('unchanged','Trả HTTP 304\nGiữ dữ liệu đã có',0,6,'end')
cache.n('json','Trả kết quả và ETag',2,6,'end')
cache.chain('start','snapshot','current').e('current','available','Có').e('current','refresh','Không')
cache.e('refresh','available').chain('available','etag').e('etag','unchanged','Có').e('etag','json','Không')
algo=Page('Tính cụm và ưu tiên','TÍNH PHÂN CỤM VÀ ĐIỂM ƯU TIÊN',
          'P(c) = [1 + tanh(Vc / 10)] × [0,34 Ec + 0,33 Fc + 0,33 Nc]. '
          'Các thành phần đã tổng hợp theo bằng chứng và bản trùng; Nc được chuẩn hóa log. '
          'Adapter hiện dùng urgency hoặc từ khóa mô tả, chưa đọc trực tiếp E_i do app gửi.')
algo.n('start','Dữ liệu cần tính lại',1,0,'start').n('active','Lấy báo cáo chưa kết thúc',1,1)
algo.n('adapter','Ánh xạ vị trí, thời gian\nvà các thuộc tính E, F, N, V',1,2,'subprocess')
algo.n('eligible','Vị trí và thời gian hợp lệ?',1,3,'decision')
algo.n('review','Đưa vào hàng cần xác minh',0,4).n('graph','Tạo trọng số đồ thị từ\nvị trí, thời gian và ngữ cảnh',1,4)
algo.n('louvain','Phân cụm bằng Louvain',1,5)
algo.n('score','Xử lý bản trùng và bằng chứng\nTính điểm ưu tiên P(c)',1,6,'subprocess')
algo.n('key','Tạo clusterKey từ ID nhỏ nhất\nSắp xếp cụm theo điểm ưu tiên',1,7)
algo.n('snapshot','Lưu snapshot, ETag\nvà thời điểm tính',1,8)
algo.n('end','Cung cấp cụm và hàng xác minh',1,9,'end')
algo.chain('start','active','adapter','eligible').e('eligible','review','Không').e('eligible','graph','Có')
algo.chain('graph','louvain','score','key','snapshot','end').e('review','snapshot')
add('flow_06_clustering_priority',cache,algo)

p=Page('Báo cáo tổng đài','ĐIỀU PHỐI VIÊN TIẾP NHẬN BÁO CÁO THỦ CÔNG',
       'Form hiện có mô tả, số liên hệ, số người và nhóm yếu thế; tọa độ là tùy chọn. '
       'Nguồn payload là hotline; nhật ký được ghi với nguồn dashboard và người thao tác. SMS Gateway có quy trình tự động riêng.')
p.n('start','Nhận cuộc gọi hoặc tin báo trực tiếp',1,0,'start').n('form','Mở form báo cáo mới trên Dashboard',1,1)
p.n('input','Nhập tình huống, số liên hệ\nvà thông tin người cần hỗ trợ',1,2)
p.n('known','Biết tọa độ?',1,3,'decision').n('coords','Nhập vĩ độ và kinh độ',0,4).n('null','Để trống vị trí\nXác minh và chấm bản đồ sau',2,4)
p.n('post','Gửi /api/reports/manual',1,5).n('valid','Dữ liệu hợp lệ?',1,6,'decision')
p.n('error','Thông báo lỗi để sửa thông tin',2,7)
p.n('save','Lưu báo cáo nguồn hotline\nGhi nhật ký người thao tác',1,7)
p.n('refresh','Làm mới danh sách và bản đồ\nBộ nhớ đệm cập nhật khi cần',1,8)
p.n('end','Báo cáo sẵn sàng để xử lý',1,9,'end')
p.chain('start','form','input','known').e('known','coords','Có').e('known','null','Không')
p.e('coords','post').e('null','post').chain('post','valid').e('valid','error','Không').e('error','input','Sửa')
p.e('valid','save','Có').chain('save','refresh','end');add('flow_07_manual_intake_location',p)

p=Page('Vòng đời điều phối','ĐIỀU PHỐI VÀ CẬP NHẬT KẾT QUẢ CỨU HỘ',
       'Giao đội không tự chuyển dispatched. Người điều phối cập nhật trạng thái riêng; có thể chọn đội khi đổi trạng thái. '
       'Phần cứu hộ thực địa nằm ngoài phần mềm; app hiện không có luồng nhận nhiệm vụ riêng cho đội cứu hộ. '
       'Mọi thay đổi chỉ được xác nhận sau khi máy chủ chấp nhận; vị trí không là điều kiện bắt buộc của API đổi trạng thái.')
p.n('start','Chọn báo cáo cần xử lý',1,0,'start').n('verify','Cần xác minh vị trí?',1,1,'decision')
p.n('location','Xác minh và bổ sung tọa độ\nLàm mới kết quả trên bản đồ',0,2,'subprocess')
p.n('team','Chọn và giao đội phụ trách',1,3).n('dispatch','Cập nhật trạng thái\n“Đã điều phối”',1,4,'subprocess')
p.n('field','Đội cứu hộ xử lý ngoài thực địa\nTrao đổi kết quả với điều phối viên',1,5,'external')
p.n('result','Kết quả được điều phối viên xác nhận?',1,6,'decision')
p.n('resolved','Cập nhật “Đã giải quyết”',0,7).n('cancelled','Đóng ca và nhập lý do',2,7)
p.n('ongoing','Giữ ca đang xử lý\nTiếp tục theo dõi',1,8)
p.n('audit','Máy chủ lưu trạng thái và nhật ký\nLoại ca đã đóng khỏi cụm hoạt động',1,9)
p.n('end','Kết thúc xử lý ca',1,10,'end')
p.chain('start','verify').e('verify','location','Có').e('location','start','Xem lại ca').e('verify','team','Không / đã xác minh')
p.chain('team','dispatch','field','result').e('result','resolved','Đã giải quyết').e('result','cancelled','Cần đóng ca')
p.e('result','ongoing','Chưa kết thúc').e('ongoing','field','Theo dõi tiếp').e('resolved','audit').e('cancelled','audit').e('audit','end')
add('flow_08_dispatch_lifecycle',p)

train=Page('Huấn luyện và đánh giá','HUẤN LUYỆN VÀ ĐÁNH GIÁ MÔ HÌNH NHẬN DIỆN ẢNH',
           'Tách rõ seed và phiên thực nghiệm; không gắn metric seed 1024 vào luồng seed 42. '
           'Tập chia đã lưu: train 1.189, validation 257, test 256. Kết quả test được báo cáo sau khi chọn checkpoint theo validation.')
train.n('start','Chọn dữ liệu và cấu hình của phiên',1,0,'start').n('split','Dùng tập chia đã lưu\nTrain / validation / test riêng biệt',1,1)
train.n('preprocess','Tiền xử lý và tăng cường ảnh\nLetterbox 256 × 256, chuẩn hóa',1,2)
train.n('model','Khởi tạo MobileNetV3-Large\nĐầu ra 4 lớp, Dropout 0,25',1,3)
train.n('warmup','Khóa backbone trong 3 epoch đầu\nSau đó mở để tinh chỉnh',1,4)
train.n('epoch','Huấn luyện một epoch bằng AdamW\nCE + 0,1 × thành phần severity',1,5)
train.n('val','Đánh giá trên validation\nCập nhật checkpoint tốt nhất',1,6)
train.n('scheduler','Điều chỉnh tốc độ học\nbằng ReduceLROnPlateau',1,7)
train.n('stop','Đủ điều kiện dừng?',1,8,'decision')
train.n('test','Nạp checkpoint đã chọn\nĐánh giá trên test độc lập',1,9)
train.n('end','Lưu kết quả đánh giá mô hình',1,10,'end')
train.chain('start','split','preprocess','model','warmup','epoch','val','scheduler','stop')
train.e('stop','epoch','Chưa').e('stop','test','Đủ epoch / dừng sớm').e('test','end')
opt=Page('Tối ưu và triển khai','ĐÁNH GIÁ CÁC NHÁNH TỐI ƯU VÀ TRIỂN KHAI DI ĐỘNG',
         'Các nhánh được so sánh riêng; không mặc định mọi nhánh nén đều được triển khai. '
         'Phương án mobile đã chọn: seed 1024, cắt tỉa, ExecuTorch/PTE. ONNX và các cấu hình khác phục vụ đối chứng. '
         'Chênh lệch metric summary/CSV của PTQ/QAT cần được giữ rõ trong diễn giải.')
opt.n('start','Checkpoint và tập đánh giá đã chốt',1,0,'start')
opt.n('baseline','Đánh giá mô hình gốc',0,2).n('prune','Đánh giá nhánh cắt tỉa',1,2).n('quant','Đánh giá PTQ / QAT',2,2)
opt.n('compare','So sánh chất lượng, dung lượng\nvà độ trễ trong từng phiên',1,3)
opt.n('export','Xuất các cấu hình cần kiểm tra\nsang ONNX hoặc ExecuTorch/PTE',1,4)
opt.n('mobile','Đo trên điện thoại\nĐối chiếu model, split và runtime',1,5)
opt.n('choose','Chọn cấu hình triển khai\ntừ bằng chứng đã lưu',1,6)
opt.n('end','Triển khai nhận diện trên thiết bị',1,7,'end')
for key in ['baseline','prune','quant']:opt.e('start',key,'Nhánh đối chứng' if key=='baseline' else 'Nhánh tối ưu').e(key,'compare')
opt.chain('compare','export','mobile','choose','end');add('flow_09_ai_training_optimization',train,opt)

# Two previously reviewed auxiliary files remain separate copies, sharing corrected detail.
add('flowchart_adaptive_mobile',copy.deepcopy(send),copy.deepcopy(image),copy.deepcopy(policy))
add('flowchart_backend_dedup',copy.deepcopy(sync),copy.deepcopy(multipart),copy.deepcopy(sms))


def base_style(kind):
    common=f'whiteSpace=wrap;html=1;align=center;verticalAlign=middle;fontFamily=Arial;fontSize=17;fontColor=#172B4D;strokeColor={STROKE};strokeWidth=1.5;spacing=10;'
    if kind=='decision':return common+'rhombus;fillColor=#FFF4D6;fontStyle=1;'
    if kind in ('start','end'):return common+'ellipse;fillColor=#E0EBF7;fontStyle=1;'
    if kind=='external':return common+'rounded=1;fillColor=#F2F2F2;dashed=1;'
    if kind=='subprocess':return common+f'shape=process;fillColor={BLUE};'
    return common+f'rounded=1;arcSize=12;fillColor={BLUE};'


def route_all(page):
    """Manhattan routing around every node; no external graph package required."""
    boxes=page.nodes
    used_ports={}
    reservations=[]
    def port(key,other,start=True):
        b,o=boxes[key],boxes[other]
        dx=(o['x']+o['w']/2)-(b['x']+b['w']/2);dy=(o['y']+o['h']/2)-(b['y']+b['h']/2)
        if abs(dy)<70: side='R' if dx>0 else 'L'
        elif dy>0:side=('B' if abs(dx)<550 else ('R' if dx>0 else 'L')) if start else ('L' if dx<=0 else 'R')
        else:side=('L' if dx<=0 else 'R') if start else 'T'
        index=used_ports.get((key,side),0);used_ports[(key,side)]=index+1
        f=[.5,.3,.7,.2,.8][index%5]
        rel={'L':(0,f),'R':(1,f),'T':(f,0),'B':(f,1)}[side]
        anchor=(round(b['x']+b['w']*rel[0],2),round(b['y']+b['h']*rel[1],2))
        delta={'L':(-24,0),'R':(24,0),'T':(0,-24),'B':(0,24)}[side]
        outside=(anchor[0]+delta[0],anchor[1]+delta[1])
        return rel,anchor,outside
    def blocked(a,b):
        for n in boxes.values():
            l,t,r,bt=n['x']-10,n['y']-10,n['x']+n['w']+10,n['y']+n['h']+10
            if a[0]==b[0] and l<a[0]<r and max(min(a[1],b[1]),t)<min(max(a[1],b[1]),bt):return True
            if a[1]==b[1] and t<a[1]<bt and max(min(a[0],b[0]),l)<min(max(a[0],b[0]),r):return True
        return False
    routes=[]
    for s,t,label,dashed in page.edges:
        sr,sa,sp=port(s,t);tr,ta,tp=port(t,s,False)
        xs={20,sp[0],tp[0]};ys={90,sp[1],tp[1]}
        for b in boxes.values():
            xs.update([b['x']-24,b['x']+b['w']+24]);ys.update([b['y']-24,b['y']+b['h']+24])
        xs=sorted(xs);ys=sorted(ys)
        xi={v:i for i,v in enumerate(xs)};yi={v:i for i,v in enumerate(ys)}
        start=(xi[sp[0]],yi[sp[1]],0);goal=(xi[tp[0]],yi[tp[1]])
        heap=[(0,0,start)];dist={start:0};previous={};end=None
        while heap:
            _,cost,state=heapq.heappop(heap)
            if cost!=dist[state]:continue
            x,y,d=state
            if (x,y)==goal:end=state;break
            for nx,ny,nd in [(x-1,y,1),(x+1,y,1),(x,y-1,2),(x,y+1,2)]:
                if not (0<=nx<len(xs) and 0<=ny<len(ys)):continue
                a=(xs[x],ys[y]);b=(xs[nx],ys[ny])
                if blocked(a,b):continue
                penalty=0
                for c,e in reservations:
                    if a[0]==b[0]==c[0]==e[0] and max(min(a[1],b[1]),min(c[1],e[1]))<min(max(a[1],b[1]),max(c[1],e[1])):penalty+=60
                    elif a[1]==b[1]==c[1]==e[1] and max(min(a[0],b[0]),min(c[0],e[0]))<min(max(a[0],b[0]),max(c[0],e[0])):penalty+=60
                    elif a[0]==b[0] and c[1]==e[1] and min(c[0],e[0])<a[0]<max(c[0],e[0]) and min(a[1],b[1])<c[1]<max(a[1],b[1]):penalty+=180
                    elif a[1]==b[1] and c[0]==e[0] and min(a[0],b[0])<c[0]<max(a[0],b[0]) and min(c[1],e[1])<a[1]<max(c[1],e[1]):penalty+=180
                nc=cost+abs(a[0]-b[0])+abs(a[1]-b[1])+(35 if d and d!=nd else 0)+penalty
                ns=(nx,ny,nd)
                if nc<dist.get(ns,math.inf):
                    dist[ns]=nc;previous[ns]=state
                    heur=abs(xs[nx]-tp[0])+abs(ys[ny]-tp[1])
                    heapq.heappush(heap,(nc+heur,nc,ns))
        if end is None:raise RuntimeError(f'No route: {page.name} {s} -> {t}')
        points=[];cur=end
        while True:
            points.append((xs[cur[0]],ys[cur[1]]))
            if cur==start:break
            cur=previous[cur]
        points.reverse();points=[sa]+points+[ta]
        compact=[]
        for pt in points:
            if compact and pt==compact[-1]:continue
            while len(compact)>=2 and ((compact[-2][0]==compact[-1][0]==pt[0]) or (compact[-2][1]==compact[-1][1]==pt[1])):compact.pop()
            compact.append(pt)
        reservations.extend(zip(compact,compact[1:]))
        routes.append((s,t,label,dashed,sr,tr,compact))
    return routes


def make_diagram(page):
    diagram=ET.Element('diagram',{'id':hashlib.sha256((page.title+page.name).encode()).hexdigest()[:12],'name':page.name})
    width=max(n['x']+n['w'] for n in page.nodes.values())+70
    bottom=max(n['y']+n['h'] for n in page.nodes.values())
    if page.lanes:width=max(x+w for _,_,x,y,w,h in page.lanes)+40;bottom=max(y+h for _,_,x,y,w,h in page.lanes)
    model=ET.SubElement(diagram,'mxGraphModel',{'dx':'1400','dy':'1000','grid':'1','gridSize':'10','guides':'1','tooltips':'1','connect':'1','arrows':'1','fold':'1','page':'0','pageScale':'1','pageWidth':str(width),'pageHeight':str(bottom+200),'math':'0','shadow':'0','background':'#FFFFFF'})
    root=ET.SubElement(model,'root');ET.SubElement(root,'mxCell',{'id':'0'});ET.SubElement(root,'mxCell',{'id':'1','parent':'0'})
    def vertex(key,text,x,y,w,h,style,parent='1'):
        c=ET.SubElement(root,'mxCell',{'id':key,'value':html.escape(text).replace('\n','<br>'),'style':style,'vertex':'1','parent':parent})
        ET.SubElement(c,'mxGeometry',{'x':str(x),'y':str(y),'width':str(w),'height':str(h),'as':'geometry'})
    vertex('title',page.title,30,15,width-60,65,'text;html=1;whiteSpace=wrap;align=center;fontFamily=Arial;fontSize=23;fontStyle=1;fontColor=#172B4D;')
    for key,title,x,y,w,h in page.lanes:
        vertex(key,title,x,y,w,h,f'swimlane;html=1;horizontal=1;startSize=44;container=1;pointerEvents=0;fillColor=#F7FAFD;swimlaneFillColor=#FFFFFF;strokeColor={STROKE};fontFamily=Arial;fontSize=17;fontStyle=1;fontColor=#172B4D;')
    for key,n in page.nodes.items():
        parent=n.get('lane') or '1';x,y=n['x'],n['y']
        if parent!='1':
            lane=next(l for l in page.lanes if l[0]==parent);x-=lane[2];y-=lane[3]
        vertex(key,n['text'],x,y,n['w'],n['h'],base_style(n['kind']),parent)
    routes=route_all(page)
    placed_labels=[]
    segments=[(i,a,b) for i,r in enumerate(routes) for a,b in zip(r[-1],r[-1][1:])]
    for i,(s,t,label,dashed,sr,tr,points) in enumerate(routes):
        style=f'edgeStyle=segmentEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;startArrow=none;endArrow=block;endFill=1;strokeColor={STROKE};strokeWidth=1.5;fontFamily=Arial;fontSize=14;fontColor=#172B4D;labelBackgroundColor=#FFFFFF;exitX={sr[0]};exitY={sr[1]};entryX={tr[0]};entryY={tr[1]};'
        if dashed:style+='dashed=1;'
        edge=ET.SubElement(root,'mxCell',{'id':f'edge_{i}','value':'','data-label':label,'style':style,'edge':'1','parent':'1','source':s,'target':t})
        g=ET.SubElement(edge,'mxGeometry',{'relative':'1','as':'geometry','x':'0','y':'-12'})
        if len(points)>2:
            ar=ET.SubElement(g,'Array',{'as':'points'})
            for x,y in points[1:-1]:ET.SubElement(ar,'mxPoint',{'x':str(x),'y':str(y)})
        if label:
            lines=textwrap.wrap(label,25,break_long_words=False) or ['']
            lw=min(210,max(48,max(len(line) for line in lines)*7.3+12));lh=22*len(lines)
            candidates=[]
            for si,(a,b) in enumerate(zip(points,points[1:])):
                if abs(a[0]-b[0])+abs(a[1]-b[1])<40:continue
                for frac in [.5,.3,.7]:
                    mx=a[0]+frac*(b[0]-a[0]);my=a[1]+frac*(b[1]-a[1])
                    if a[1]==b[1]:positions=[(mx-lw/2,my-lh-5),(mx-lw/2,my+5)]
                    else:positions=[(mx+7,my-lh/2),(mx-lw-7,my-lh/2)]
                    for lx,ly in positions:
                        rect=(lx,ly,lx+lw,ly+lh);penalty=0
                        for n in page.nodes.values():
                            if max(rect[0],n['x']-5)<min(rect[2],n['x']+n['w']+5) and max(rect[1],n['y']-5)<min(rect[3],n['y']+n['h']+5):penalty+=10000
                        for other in placed_labels:
                            if max(rect[0],other[0]-5)<min(rect[2],other[2]+5) and max(rect[1],other[1]-5)<min(rect[3],other[3]+5):penalty+=10000
                        for ei,c,d in segments:
                            if ei==i:continue
                            if c[0]==d[0] and rect[0]<c[0]<rect[2] and max(rect[1],min(c[1],d[1]))<min(rect[3],max(c[1],d[1])):penalty+=300
                            if c[1]==d[1] and rect[1]<c[1]<rect[3] and max(rect[0],min(c[0],d[0]))<min(rect[2],max(c[0],d[0])):penalty+=300
                        if lx<0 or ly<90 or lx+lw>width:penalty+=10000
                        candidates.append((penalty+si*2,lx,ly,rect))
            if candidates:
                _,lx,ly,rect=min(candidates);placed_labels.append(rect)
                vertex(f'label_{i}','\n'.join(lines),lx,ly,lw,lh,'text;html=1;whiteSpace=wrap;align=center;verticalAlign=middle;spacing=0;fontFamily=Arial;fontSize=14;fontColor=#172B4D;fillColor=#FFFFFF;strokeColor=none;')
    # Keep label backgrounds clear of rectangular node bounds, including the
    # empty corners of diamonds. Labels remain editable separate text objects.
    text_cells=[c for c in root if (c.get('id') or '').startswith('label_')]
    occupied=[]
    for c in text_cells:
        g=c.find('mxGeometry');x,y,w,h=[float(g.get(k)) for k in ('x','y','width','height')]
        choices=[]
        for dx in range(-72,73,6):
            for dy in range(-72,73,6):
                a,b=x+dx,y+dy;rect=(a,b,a+w,b+h)
                if a<10 or a+w>width-10:continue
                if any(max(rect[0],n['x']-4)<min(rect[2],n['x']+n['w']+4) and max(rect[1],n['y']-4)<min(rect[3],n['y']+n['h']+4) for n in page.nodes.values()):continue
                if any(max(rect[0],r[0]-4)<min(rect[2],r[2]+4) and max(rect[1],r[1]-4)<min(rect[3],r[3]+4) for r in occupied):continue
                choices.append((abs(dx)+abs(dy),abs(dx),a,b,rect))
        if choices:
            _,_,a,b,rect=min(choices);g.set('x',str(a));g.set('y',str(b));occupied.append(rect)
        else:occupied.append((x,y,x+w,y+h))
    vertex('scope_note',page.note,40,bottom+45,width-80,120,'rounded=1;whiteSpace=wrap;html=1;align=left;verticalAlign=middle;spacing=14;fontFamily=Arial;fontSize=15;fontColor=#44546A;fillColor=#F5F7FA;strokeColor=#D5DFEB;')
    return diagram


def main():
    bundle=ET.Element('mxfile',{'host':'app.diagrams.net','agent':'Codex','version':'32.6.1'})
    for stem,pages in PAGES.items():
        document=ET.Element('mxfile',{'host':'app.diagrams.net','agent':'Codex','version':'32.6.1'})
        for page in pages:
            d=make_diagram(page);document.append(d)
            merged=copy.deepcopy(d);merged.set('name',f'{stem} · {page.name}');bundle.append(merged)
        ET.indent(document)
        ET.ElementTree(document).write(OUT/'edited'/f'{stem}.drawio',encoding='utf-8',xml_declaration=True)
        print(stem,len(pages),'pages')
    ET.indent(bundle)
    ET.ElementTree(bundle).write(OUT/'00-flowcharts-reviewed.drawio',encoding='utf-8',xml_declaration=True)
    (OUT/'checks'/'page-index.json').write_text(json.dumps({stem:[p.name for p in pages] for stem,pages in PAGES.items()},ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':main()
