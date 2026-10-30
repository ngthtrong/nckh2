#!/usr/bin/env python3
"""Build the offline defense deck from repository evidence; no experiments run."""
from pathlib import Path
from collections import defaultdict
import base64
import csv
import hashlib
import html
import json
import statistics

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
N = '#101B2D'
B = '#2B5FA8'
O = '#A3430F'
M = '#5A6270'
L = '#DCE7F6'
SOURCES = {
    'paper': 'paper/main.tex',
    'paper_pdf': 'paper/main.pdf',
    'reference': 'PLM + MCNN for Neoantigen Prediction.html',
    'benchmark': 'thucnghiem/results/cij_baseline_benchmark_results/benchmark_summary.csv',
    'stress': 'thucnghiem/results/rq1_results/aggregate/rq1_stress_summary.csv',
    'alignment': 'thucnghiem/results/rq2_results/rq2_summary.csv',
    'robustness': 'thucnghiem/results/rq2_results/rq2_robustness_test.csv',
    'dispatch': 'thucnghiem/results/rq3_results/rq3_dispatch_test.csv',
    'paired': 'thucnghiem/results/rq3_results/rq3_paired_comparisons_seed.csv',
}


def rows(key):
    with (ROOT / SOURCES[key]).open() as f:
        return list(csv.DictReader(f))


def esc(s):
    return html.escape(str(s))


def text(x, y, s, size=24, fill=N, anchor='start', weight=400):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{esc(s)}</text>'


def line(x1, y1, x2, y2, color=B, width=3, dash=''):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}" stroke-dasharray="{dash}"/>'


def rect(x, y, w, h, fill=L, stroke='none', r=16):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'


def circle(x, y, r=13, fill=B, stroke='none'):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="3"/>'


def svg(body, label, w=1380, h=420):
    return f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}"><title>{esc(label)}</title>{body}</svg>'


def card(kicker, title, body, cls=''):
    return f'<article class="card {cls}"><p class="tag">{kicker}</p><h3>{title}</h3><div>{body}</div></article>'


def grid(*cards, cls=''):
    return '<div class="grid '+cls+'">'+''.join(cards)+'</div>'


def table(headers, data, cls=''):
    return '<table class="'+cls+'"><thead><tr>'+''.join('<th>'+c+'</th>' for c in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(c)+'</td>' for c in r)+'</tr>' for r in data)+'</tbody></table>'


def pills(*items):
    return '<div class="pills">'+''.join('<span>'+i+'</span>' for i in items)+'</div>'


def points_chart(data, title, domain=(0, 1), ticks=None, h=360):
    # data = label, mean, lower, upper, highlight. Bounds come from source CSV.
    x0, x1 = 450, 1160
    X = lambda v: x0+(v-domain[0])/(domain[1]-domain[0])*(x1-x0)
    s = text(x0, 25, title, 24, M)
    ticks = ticks or [0, .2, .4, .6, .8, 1]
    for v in ticks:
        x = X(v)
        s += line(x, 45, x, h-45, '#D9DEE6', 1)+text(x, h-12, f'{v:g}', 21, M, 'middle')
    gap = (h-105)/len(data)
    for i, (label, v, lo, hi, active) in enumerate(data):
        y = 68+i*gap
        col = O if active else B
        s += text(8, y+8, label, 25, N, weight=700 if active else 400)
        s += line(X(lo), y, X(hi), y, col, 4)+line(X(lo), y-8, X(lo), y+8, col, 3)+line(X(hi), y-8, X(hi), y+8, col, 3)
        s += circle(X(v), y, 8, col)+text(1210, y+8, f'{v:.4f}', 26, col, weight=700)
    return svg(s, title+'; chấm là trung bình, thanh là khoảng tin cậy bootstrap 95%.', h=h)


def scenario_art():
    s = rect(0, 0, 1380, 405, '#FFFFFF', '#D9DEE6')
    s += '<path d="M0 270 Q230 180 470 275 T950 200 T1380 280" fill="none" stroke="#DCE7F6" stroke-width="75"/>'
    clusters = [(210,140, B,'A · Tin báo lặp'), (620,135, O,'B · Sự cố gần A'), (1100,150,M,'C · Báo cáo giả')]
    for cx, cy, col, label in clusters:
        s += f'<ellipse cx="{cx}" cy="{cy}" rx="112" ry="65" fill="none" stroke="{col}" stroke-width="3" stroke-dasharray="8 7"/>'
        for dx,dy in [(-50,-12),(0,-25),(38,9),(-18,28)]:
            s+=circle(cx+dx,cy+dy,12,col)
        s+=text(cx,cy+105,label,27,col,'middle',700)
    s+=rect(590,310,210,63,N)+text(695,351,'Đội cứu hộ',25,'#FFFFFF','middle',700)
    s+=text(38,365,'Sơ đồ minh họa · không phải bản đồ hoặc mẫu thực nghiệm',21,M)
    return svg(s,'Tình huống minh họa gồm tin báo lặp, hai sự cố gần nhau và báo cáo giả.',h=405)


def pipeline_art():
    s=''
    for i,(a,b) in enumerate([('01','Tin báo'),('02','Đồ thị & cụm'),('03','Điểm ưu tiên'),('04','Lịch điều phối')]):
        x=i*350
        s+=rect(x,30,305,145,N if i==2 else '#FFFFFF','#D9DEE6')
        s+=text(x+25,70,a,23,'#F0904F' if i==2 else O,weight=700)
        s+=text(x+152,125,b,28,'#FFFFFF' if i==2 else N,'middle',700)
        if i<3:
            s+=line(x+309,105,x+340,105,B,4)+f'<path d="M{x+332} 96 l10 9 -10 9" fill="none" stroke="{B}" stroke-width="4"/>'
    s+=line(150,177,150,235,O,3)+rect(0,235,303,90,'#FBE9DA')+text(150,273,'Thiếu vị trí / thời gian',24,O,'middle')+text(150,307,'→ Kiểm tra thủ công',24,O,'middle')
    s+=rect(422,235,600,90,'#DCE7F6')+text(722,273,'Incident ID · Benefit · Deadline · Harm',24,B,'middle',700)+text(722,307,'Nhãn đánh giá giữ riêng',23,B,'middle')
    s+=line(1025,280,1200,280,M,3,'8 8')+rect(1100,235,280,90,'#FFFFFF','#D9DEE6')+text(1240,273,'Đánh giá ngoại tuyến',24,N,'middle',700)+text(1240,307,'sau khi khóa lịch',23,M,'middle')+line(1200,178,1200,230,B,3)
    return svg(s,'Pipeline chỉ dùng đầu vào quan sát được. Nhãn đánh giá nối vào sau khi lịch đã khóa.',h=350)


benchmark = {r['method']:r for r in rows('benchmark')}
stress = {(r['method'],r['scenario']):float(r['ari_original_mean']) for r in rows('stress')}
alignment = {r['method']:r for r in rows('alignment') if r['section']=='alignment' and r['metric']=='ndcg_at_5'}
robust = defaultdict(list)
for r in rows('robustness'):
    robust[r['scenario'],r['estimator']].append(float(r['priority_drift_abs_normalized']))
dispatch = defaultdict(list)
for r in rows('dispatch'):
    if r['partition']=='product_cij':
        for metric in ['latent_harm','deadline_miss_rate']:
            dispatch[r['resource_scenario'],r['policy'],metric].append(float(r[metric]))
paired = {(r['comparator'],r['metric']):r for r in rows('paired') if r['dimension']=='policy' and r['candidate']=='revised_priority' and json.loads(r['fixed']).get('partition')=='product_cij'}


def heatmap():
    methods=[('product_cij_louvain','Product Louvain'),('additive_cij_louvain','Additive Louvain'),('additive_cij_louvain_matched_density','MD Additive'),('product_cij_leiden','Product Leiden'),('geo_time_dbscan','Geo-time DBSCAN')]
    scenarios=[('baseline','Gốc'),('gps_noise_100m','GPS 100 m'),('gps_noise_300m','GPS 300 m'),('time_noise_15min','Giờ 15 min'),('time_noise_60min','Giờ 60 min'),('exact_transport_copy_2x','Bản sao 2×'),('exact_transport_copy_5x','Bản sao 5×')]
    s=text(0,24,'ARI trung bình trên 40 test runs · cùng thang màu 0 → 1',24,M)
    for j,(_,name) in enumerate(scenarios): s+=text(345+j*146,70,name,21,N,'middle',700)
    for i,(method,name) in enumerate(methods):
        y=90+i*67
        s+=text(0,y+38,name,24,N,weight=700 if i==0 else 400)
        for j,(sc,_) in enumerate(scenarios):
            v=stress[method,sc]; t=v
            rgb=tuple(round(247+(c-247)*t) for c in (43,95,168))
            s+=rect(275+j*146,y,140,60,'rgb'+str(rgb),r=5)+text(345+j*146,y+38,f'{v:.3f}',24,'#FFFFFF' if v>.61 else N,'middle',700)
    for j in range(11):
        v=j/10;rgb=tuple(round(247+(c-247)*v) for c in (43,95,168))
        s+=rect(850+j*35,445,35,16,'rgb'+str(rgb),r=0)
    s+=text(823,460,'0',20,M)+text(1255,460,'1',20,M)
    return svg(s,'ARI theo năm phương pháp và bảy điều kiện; giá trị tuyệt đối, không phải kiểm định giữa phương pháp.',h=480)


def drift_chart():
    scs=[('exact_duplicate_2x','Bản sao 2×'),('exact_duplicate_5x','Bản sao 5×'),('exact_duplicate_10x','Bản sao 10×'),('coordinated_high_confidence','Chiến dịch phối hợp')]
    # Source scenario names are resolved explicitly, never silently substituted.
    campaign=[s for s,e in robust if 'coordinated' in s]
    assert len(set(campaign))==1, campaign
    scs[-1]=(campaign[0],scs[-1][1])
    s=text(0,25,'Độ trôi ưu tiên chuẩn hóa trung bình · thấp hơn là tốt hơn',24,M)
    X=lambda v:380+v/.2*850
    for v in [0,.05,.10,.15,.20]:
        s+=line(X(v),55,X(v),385,'#D9DEE6',1)+text(X(v),420,f'{v:.2f}',21,M,'middle')
    for i,(sc,label) in enumerate(scs):
        y=70+i*80
        s+=text(0,y+30,label,25,N,weight=700 if i==3 else 400)
        for j,(method,col) in enumerate([('duplicate_aware_robust',O),('legacy_raw',B)]):
            vals=robust[sc,method];assert vals
            v=statistics.mean(vals)
            s+=rect(380,y+j*29,max(0.0,X(v)-380),20,col,r=3)
            if v==0:s+=circle(380,y+j*29+10,4,col)
            s+=text(X(v)+15,y+j*29+18,f'{v:.4f}',23,col,weight=700)
    s+=circle(920,455,7,O)+text(936,463,'Revised',23,O)+circle(1100,455,7,B)+text(1116,463,'Legacy',23,B)
    return svg(s,'So sánh độ trôi ưu tiên Revised và Legacy khi nhân bản và tấn công phối hợp.',h=480)


def dispatch_chart():
    s=''
    scenarios=[('lean_hue','Lean Hue'),('nominal_dual_depot','Nominal'),('regional_surge','Surge')]
    available={k[0] for k in dispatch}
    assert {x[0] for x in scenarios}==available,available
    pols=[('revised_priority','Revised',O),('legacy_priority','Legacy',B),('nearest_first','Nearest',M)]
    for panel,(metric,title,maximum) in enumerate([('latent_harm','Điểm harm mô phỏng ↓',800),('deadline_miss_rate','Tỷ lệ trễ hạn (%) ↓',1)]):
        off=panel*700
        s+=text(off+10,28,title,28,N,weight=700)
        for t in range(5):
            v=maximum*t/4;y=340-v/maximum*260
            s+=line(off+65,y,off+660,y,'#D9DEE6',1)+text(off+50,y+7,str(round(v*100)) if metric=='deadline_miss_rate' else str(int(v)),19,M,'end')
        for j,(sc,label) in enumerate(scenarios):
            gx=off+95+j*195
            for k,(policy,name,col) in enumerate(pols):
                vals=dispatch[sc,policy,metric];assert len(vals)==40
                v=statistics.mean(vals); bh=v/maximum*260;x=gx+k*54
                s+=rect(x,340-bh,42,bh,col,r=3)+text(x+21,328-bh,f'{v*100:.1f}' if metric=='deadline_miss_rate' else f'{v:.1f}',19,col,'middle',700)
            s+=text(gx+75,378,label,23,N,'middle',700)
    for i,(_,name,col) in enumerate(pols):
        x=365+i*245;s+=rect(x,425,20,20,col,r=2)+text(x+32,443,name,25,col)
    return svg(s,'Trung bình mô tả harm và tỷ lệ trễ hạn theo ba điều kiện nguồn lực, mỗi điều kiện gồm 40 test seeds.',h=470)


slides=[]


def add(section,title,body,take='',note='',source='paper',cls='',appendix=False):
    slides.append(dict(section=section,title=title,body=body,take=take,note=note,source=source,cls=cls,appendix=appendix))


add('Bảo vệ bài báo · Bản thảo trình bày 01','Kiểm thử gom cụm<br>và xếp hạng tin báo<br>cứu hộ lũ lụt',
    '<p class="cover-sub">Stress-Testing Product-Gated Clustering and Bounded Priority Ranking for Flood-Rescue Reports: A Synthetic Study</p><div class="cover-meta"><b>Thanh-Trong Nguyen và cộng sự</b><span>Trường CNTT & Truyền thông · Đại học Cần Thơ</span><span>Đề tài THS2026-68</span></div><div class="cover-art">'+pipeline_art()+'</div>',
    note='Mở đầu: Bài báo kiểm tra liệu các bảo đảm ở bước gom cụm và tính điểm có chuyển thành kết quả điều phối tốt hơn trong mô phỏng hay không. Đây là nghiên cứu trên dữ liệu bán tổng hợp và tổng hợp. Không giới thiệu như một chính sách cứu hộ đã được xác nhận.',cls='cover dark')

add('I · Vấn đề nghiên cứu','Nhiều tin báo, nhưng có bao nhiêu sự cố?',scenario_art()+pills('Trùng lặp','Sự cố gần nhau','Báo cáo giả','Nguồn lực hữu hạn'),
    'Gom sai sự cố hoặc ưu tiên sai có thể làm thay đổi lịch điều phối.',
    'Dùng hình minh họa: A có nhiều bản sao, B gần A nhưng là sự cố khác, C là nhóm báo cáo giả. Đặt câu hỏi: một đội cứu hộ nên đi đâu trước? Hình là sơ đồ minh họa, không phải dữ liệu hay bản đồ thực nghiệm.')

add('I · Khoảng trống & câu hỏi nghiên cứu','Ba tầng cần ba phép đánh giá',grid(
    card('RQ1 · Gom cụm','Product có tốt hơn Additive?','<p>So sánh các pipeline được hiệu chỉnh độc lập.</p><div class="metric">ARI <span>↑</span></div><p>Khớp với nhãn sự cố.</p>'),
    card('RQ2 · Xếp hạng','Điểm có khớp lợi ích?','<p>Đồng chỉnh với benefit sinh độc lập; kiểm thử nhiễu và trùng lặp.</p><div class="metric">NDCG@5 <span>↑</span></div><p>Chất lượng thứ tự ưu tiên.</p>'),
    card('RQ3 · Điều phối','Lỗi lan vào lịch thế nào?','<p>Đánh giá tách, gộp, đích giả trên cụm dự đoán.</p><div class="metric">Harm · Trễ hạn <span>↓</span></div><p>Hệ quả trong mô phỏng.</p>')),
    'Gom cụm đúng, điểm ổn định và điều phối tốt là ba thuộc tính cần kiểm tra riêng.',
    'Khoảng trống của bài: các tài nguyên được thảo luận chưa cung cấp đồng thời nhãn liên kết sự cố, ưu tiên cứu hộ và kết quả điều phối. Đọc ba RQ trước khi giới thiệu công thức. ARI là mức đồng thuận phân hoạch đã hiệu chỉnh ngẫu nhiên, không phải phần trăm đúng. NDCG@5 đo chất lượng xếp hạng năm vị trí đầu so với benefit lý tưởng.')

add('I · Đóng góp','Xác lập tính chất và đo giới hạn',grid(
    card('01 · Gom cụm','Chặn khoảng cách cạnh','<p>Product gating cho một chặn không gian có thể kiểm tra khi ngưỡng dương hợp lệ.</p>'),
    card('02 · Xếp hạng','Bất biến với bản sao','<p>Tổng hợp theo họ bằng chứng giữ điểm trước bản sao chính xác khi nhóm và đầu vào cố định.</p>'),
    card('03 · Điều phối','Đánh giá hệ quả','<p>Khóa lịch trên cụm dự đoán, rồi đo harm và deadline misses bằng truth giữ riêng.</p>')),
    'Đóng góp gồm bảo đảm có điều kiện và các kết quả thực nghiệm chỉ ra giới hạn.',
    'Không gắn đóng góp với một tuyên bố phương pháp luôn thắng. Phần mới cần bảo vệ là cách kiểm tra phạm vi của từng tính chất và đo hệ quả phía sau. Các kết quả bất lợi vẫn trả lời các giả thuyết nghiên cứu, nhưng không tự tạo thành bằng chứng hiệu quả ứng dụng.')

add('II · Dữ liệu · 1/3','Một bộ bán tổng hợp, một bộ tổng hợp',grid(
    card('RQ1 · Generator 3.0','Bán tổng hợp','<div class="number">26.288 <small>tin báo</small></div><p><b>Bối cảnh địa lý:</b> EMSR848, OSM, WorldPop.</p><p><b>Được sinh:</b> sự cố, tin báo, bản sao, tấn công và nhãn.</p><div class="small-rule"></div><p>80 runs · 16 sự cố ẩn/run.</p>'),
    card('RQ2 / RQ3 · Candidate 4.1','Hoàn toàn tổng hợp','<div class="number">30.229 <small>tin báo</small></div><p><b>Được sinh:</b> hình học, sự cố, tin báo và nhãn.</p><p><b>Kết quả mô phỏng:</b> benefit, deadline, service, access, harm.</p><div class="small-rule"></div><p>80 datasets · 16 sự cố/dataset.</p>')),
    'Bối cảnh địa lý thực chỉ hỗ trợ tính hợp lý của bối cảnh; tin báo và kết quả vẫn được sinh.',
    'Nói rõ ngay từ đầu thay vì để hội đồng tự phát hiện ở cuối. WorldPop là bề mặt dân số, không phải số người mắc kẹt được quan sát. Candidate 4.1 không được mô tả là neo vào EMSR848. Tổng số 26.288 và 30.229 tính trên cả ba phần chia, không phải số mẫu test. Hai bộ riêng không được cộng thành một benchmark duy nhất.')

add('II · Dữ liệu · 2/3','Vì sao lựa chọn dữ liệu được sinh?',grid(
    card('Khoảng trống nhãn','Cần đúng loại ground truth','<p>RQ1 cần cùng/khác sự cố; RQ2 cần benefit độc lập; RQ3 cần điều kiện nguồn lực và kết quả.</p><p>CrisisMMD/FloodNet được thảo luận trong bài chưa cung cấp đồng thời bộ nhãn đó.</p>'),
    card('Kiểm thử có kiểm soát','Biết điều gì đã thay đổi','<p>Chủ động điều chỉnh GPS, timestamp, số bản sao và kiểu tấn công.</p><p>Giữ cấu hình, ghép theo run/seed và lặp lại cùng kịch bản.</p>'),
    card('Cô lập từng tầng','Tách nguồn gây sai lệch','<p>RQ1 đo gom cụm.</p><p>RQ2 dùng nhóm sự cố chuẩn của bộ sinh để cô lập xếp hạng.</p><p>RQ3 dùng cụm dự đoán để đo hệ quả.</p>')),
    'Lựa chọn này phù hợp cho kiểm thử cơ chế có kiểm soát, với phạm vi kết luận giới hạn ở mô phỏng.',
    'Đây là lý do phương pháp luận được hỗ trợ bởi thiết kế trong bài, không phải tuyên bố không tồn tại dữ liệu thực ở mọi nơi. Không nói đã kiểm thử dữ liệu thực hay đã thử thay thế dữ liệu. Hai bộ có vai trò đánh giá khác nhau; điều đó không chứng minh tính độc lập ngoài miền hoặc hợp thức hóa kết luận xuyên hai bộ.')

add('II · Dữ liệu · 3/3','Bất lợi ảnh hưởng trực tiếp đến kết luận',table(
    ['Bất lợi','Hệ quả đối với bằng chứng'],[
        ['<b>Phân bố do generator quyết định</b>','Đổi seed vẫn ở trong cùng cơ chế sinh; chưa kiểm chứng ngoài phân bố.'],
        ['<b>Benefit và harm được mô phỏng</b>','Kết quả phụ thuộc giả định sinh và đánh giá; chưa đo lợi ích cứu hộ thực.'],
        ['<b>Hai bộ riêng cho các RQ</b>','Chưa có một chuỗi kiểm chứng trên cùng mẫu cho cả ba RQ.'],
        ['<b>Thiếu snapshot/lineage của neo địa lý</b>','Khó kiểm tra đầy đủ nguồn gốc và tính đại diện của phần bối cảnh.'],
        ['<b>RQ1 hiện có đủ vị trí/thời gian/F/E</b>','Nhánh xử lý thiếu dữ liệu đã đặc tả; độ bền thiếu dữ liệu chưa được đo trong benchmark RQ1.'],
    ]),
    'Kết luận được giới hạn ở hai generator và các cấu hình đã thử.',
    'Không diễn đạt rằng dữ liệu tổng hợp tự nó vô giá trị. Nó hỗ trợ kiểm thử có kiểm soát nhưng không xác định được tỷ lệ lỗi hay hiệu quả ngoài thực địa. Nhấn mạnh sự khác nhau giữa tổng hợp bối cảnh, tổng hợp tin báo và tổng hợp kết quả. RQ1 có bối cảnh bán tổng hợp, còn incident/report labels và outcomes là mô phỏng.')

add('II · Pipeline & ranh giới thông tin','Thuật toán không được xem nhãn đánh giá',pipeline_art()+
    '<p class="caption">Đầu vào gọn: L · T · F · E · N · V · Q — vị trí, thời gian, ngập, khẩn cấp, số người, dễ tổn thương, confidence.</p>',
    'Truth chỉ được nối vào sau dự đoán/lập lịch; Q là heuristic, chưa được hiệu chuẩn thành xác suất đúng.',
    'Giới thiệu L và T trước vì cần để tính khoảng cách và độ lệch thời gian. F/E là evidence đầu vào của nghiên cứu thuật toán, không coi chúng là bằng chứng extractor ngoài thực tế đã chính xác. Q dựa ảnh và corroboration từ payload quan sát được. Manual-review là ranh giới thiết kế; benchmark RQ1 hiện chưa thực thi stress thiếu L/T.')

add('II · Thiết kế đánh giá','Khóa lựa chọn trước khi mở tập test',
    '<div class="split"><div><b>20</b><span>Development</span></div><div><b>20</b><span>Calibration</span></div><div><b>40</b><span>Test giữ lại</span></div></div>'+grid(
    card('RQ1','Hiệu chỉnh độc lập','<p>Product và Additive chọn cấu hình trên calibration theo ARI.</p><p>Thêm Additive cùng mật độ để chẩn đoán ảnh hưởng mật độ cạnh.</p>'),
    card('RQ2 / RQ3','Hai phạm vi đánh giá','<p>RQ2: oracle grouping để đo riêng điểm.</p><p>RQ3: predicted clusters; gộp ba điều kiện nguồn lực trong từng seed → 40 cặp.</p>')),
    'Các phép so sánh dùng cùng test runs/seeds và hiệu chỉnh đa so sánh theo các họ kiểm định.',
    'Mỗi bộ có split 20/20/40 riêng. Oracle grouping nghĩa là dùng nhóm sự cố đúng của mô phỏng chỉ trong RQ2 để loại sai số gom cụm khỏi phép đánh giá điểm. Không cho scheduler xem oracle. RQ3 không dùng 120 mẫu độc lập vì ba resource scenarios của cùng seed có phụ thuộc. Bootstrap và Wilcoxon/Holm trả lời các câu hỏi khác nhau.')

add('III · RQ1 · Phương pháp','Product dùng khoảng cách làm cổng',grid(
    card('Product','Xa → trọng số bị giảm','<div class="formula">w× = G (βT + γC)</div><p>G: tương đồng không gian.</p><p>T: tương đồng thời gian.</p><p>C: tương đồng ngập và khẩn cấp.</p>','blue'),
    card('Additive','Cộng các nguồn tương đồng','<div class="formula">w+ = αG + βT + γC</div><p>Khi xa nhau, thời gian/ngữ cảnh vẫn có thể đóng góp trọng số.</p><p>So sánh chính là hai pipeline đã hiệu chỉnh độc lập.</p>')),
    'Sau tính trọng số: lọc theo quantile → giữ top-k ở từng đầu mút → hợp cạnh → Louvain/Leiden.',
    'Công thức rút gọn cho trường hợp đã có L/T và contextual inputs, đúng với benchmark RQ1 hiện tại. G là Gaussian theo khoảng cách; T là suy giảm mũ theo chênh thời gian; C là tương đồng ngữ cảnh. Không mô tả so sánh pipeline tinh chỉnh độc lập là tác động nhân quả riêng của toán tử nhân.')

art=''
for i in range(7):
    if i<6:art+=line(170+i*165,155,335+i*165,155,B,5)
    art+=circle(170+i*165,155,19,B)
art+=line(170,235,1160,235,O,3)+text(665,280,'Mỗi cạnh ngắn; chuỗi nhiều cạnh vẫn có thể kéo dài',29,O,'middle',700)
add('III · RQ1 · Tính chất','Chặn cạnh không tự chặn đường kính cụm',
    '<div class="equation-band">w× &gt; θ &nbsp; ⇒ &nbsp; d &lt; σ √[2 log((β + γ) / θ)]</div>'+svg(art,'Chuỗi cạnh ngắn vẫn có thể tạo cụm kéo dài.',h=310)+pills('Điều kiện: 0 < θ < β + γ','Đường kính cụm còn phụ thuộc số bước h'),
    'Đây là bảo đảm toán học có điều kiện; chất lượng phân cụm vẫn cần kiểm chứng thực nghiệm.',
    'Đặt B=β+γ. Vì T,C≤1, w×≤B exp(-d²/(2σ²)); với 0<θ<B suy ra chặn. Kết quả nói về từng cạnh được giữ. Muốn chặn đường kính cụm còn cần hop diameter quan sát được h; pipeline không kiểm soát trước h. Không diễn giải định lý là Product phải đạt ARI tốt hơn.')

labels=[('additive_cij_louvain','Additive Louvain'),('product_cij_leiden','Product Leiden'),('product_cij_louvain','Product Louvain'),('additive_cij_louvain_matched_density','MD Additive'),('coordinate_kmeans','Coordinate K-means')]
bc=[(name,float(benchmark[k]['ari_mean']),float(benchmark[k]['ari_ci95_low']),float(benchmark[k]['ari_ci95_high']),k=='product_cij_louvain') for k,name in labels]
add('III · RQ1 · Kết quả','Chưa xác lập ưu thế của Product',points_chart(bc,'ARI · cao hơn là tốt hơn · 40 test runs')+
    '<div class="statrow"><span>Product − Additive <b>−0,01184</b></span><span>Wilcoxon + Holm <b>p = 0,2560</b></span><span>ARI ≠ tỷ lệ phần trăm đúng</span></div>',
    'Additive có ARI trung bình cao nhất; chưa xác lập ưu thế của Product trong tương phản chính.',
    'Thanh ngang là khoảng tin cậy bootstrap 95% riêng từng phương pháp. Không dùng độ chồng lấn của các khoảng này để thay kiểm định ghép. Chênh lệch Product−Additive có CI bootstrap chưa hiệu chỉnh [-0.02257,-0.00240] nhưng Wilcoxon/Holm p=.2560; khác phương pháp và hiệu chỉnh nên không đọc như một kiểm định duy nhất. Bảng đầy đủ ở phụ lục.',source='benchmark')

add('III · RQ1 · Stress tests','Bản sao 5× làm suy giảm mạnh gom cụm',heatmap(),
    'Bất biến của điểm ưu tiên khi nhóm cố định chưa bảo đảm gom cụm bất biến trước bản sao.',
    'Màu và số là ARI tuyệt đối từ primary stress CSV, chỉ tính các báo cáo gốc có incident labels để giữ đơn vị đánh giá giữa các multiplicities. GPS là sigma nhiễu độc lập trên mỗi trục địa phương; time là sigma phút. Bản sao 2x tăng nhẹ, 5x giảm mạnh, không suy ngưỡng sụp đổ hoặc xu hướng đơn điệu. Các mức này là stress có kiểm soát, không phải tần suất thực địa. MD = matched density.',source='stress')

add('III · RQ2 · Phương pháp','Một bản sao không tạo thêm bằng chứng',
    '<div class="copyflow"><div><span class="copy">Tin gốc</span><span class="copy">Bản sao</span><span class="copy">Bản sao</span></div><b>→</b><div class="family">Một họ<br>bằng chứng</div><b>→</b><div class="family darkbox">Một điểm<br>có chặn</div></div>'+grid(
    card('Family-wise','Giảm ảnh hưởng số bản sao','<p>Dùng cực đại trong họ bằng chứng; giữ nhóm và đầu vào thì bản sao chính xác không đổi điểm.</p>'),
    card('Bounded','Giới hạn khuếch đại','<p>Clipping, log và tanh làm bão hòa từng phần.</p><p>Điểm P nằm trong [0, μ], với 1 ≤ μ ≤ 2.</p>')),
    'Điểm có chặn và bất biến bản sao là tính chất của công thức, chưa xác nhận thứ tự ưu tiên đúng.',
    'Họ bằng chứng được hình thành bởi fingerprint exact và connected components cho near duplicates. Không đánh đồng họ fingerprint với nguồn độc lập đã xác thực. Max không đếm các báo cáo chồng lấn như những người khác nhau, nhưng có thể bỏ sót nhu cầu ở các trường hợp khác. Không hứa chống mọi tấn công.')

al=[]
for key,label in [('random','Random'),('population_only','Population-only'),('duplicate_aware_robust','Revised'),('legacy_raw','Legacy')]:
    r=alignment[key];lo,hi=json.loads(r['paired_confidence_interval']);al.append((label,float(r['mean']),lo,hi,key=='duplicate_aware_robust'))
add('III · RQ2 · Kết quả','Chưa xác lập đồng chỉnh với lợi ích',points_chart(al,'NDCG@5 · cao hơn là tốt hơn · 40 test seeds',h=340)+
    '<div class="statrow"><span>Revised <b>0,6669</b></span><span>Random <b>0,6763</b></span><span>Revised − Legacy <b>+0,0121</b> · Holm p = 0,5882</span></div>',
    'Ngay khi đã cho nhóm sự cố đúng, điểm revised chưa thể hiện lợi thế đồng chỉnh tổng quát.',
    'Giải thích NDCG@5: so sánh chất lượng năm vị trí đầu với thứ tự benefit lý tưởng. Benefit là nhãn sinh độc lập trong mô phỏng, không phải đánh giá chuyên gia hay lợi ích quan sát được ngoài hiện trường. Revised có point estimate thấp hơn random/population-only; không tuyên bố random thắng có ý nghĩa thống kê từ hai trung bình. CI bootstrap 95%.',source='alignment')

add('III · RQ2 · Stress tests','Bất biến bản sao có phạm vi hẹp',drift_chart(),
    'Chiến dịch báo cáo phối hợp có confidence cao vẫn gây độ trôi lớn dù điểm bị chặn.',
    'Độ trôi = trị tuyệt đối thay đổi điểm được chuẩn hóa, không phải xác suất tin giả. Mỗi kịch bản hiển thị có 40 perturbations/estimator. Các thanh chỉ mô tả trung bình, không có CI cho từng thanh. Exact 2x/5x/10x cho revised drift 0 khi nhóm và input cố định. Campaign: revised≈.1688, legacy≈.0309. Hiệu số độ trôi +.1379 bất lợi cho revised; Holm p≈9.1e-12 từ bài.',source='robustness')

add('III · RQ3 · Thiết kế','Lập lịch trên các cụm được dự đoán',grid(
    card('Đầu vào','Đích đến có thể sai','<p><b>Tách:</b> một sự cố thành nhiều đích.</p><p><b>Gộp:</b> nhiều sự cố thành một đích.</p><p><b>Đích giả:</b> tạo chuyến đi không phục vụ sự cố thật.</p>'),
    card('Đối chứng','Cùng điều kiện nguồn lực','<p>Revised priority</p><p>Legacy priority</p><p>Nearest-first</p><div class="small-rule"></div><p>Lean Hue · Nominal dual depot · Regional surge.</p>'),
    card('Đánh giá','Truth nối sau lịch','<p>Harm mô phỏng và deadline misses.</p><p>Ba điều kiện được lấy trung bình trong từng seed.</p><div class="number">40 <small>cặp seed độc lập</small></div>')),
    'RQ3 đo hệ quả của cả cụm dự đoán và chính sách ưu tiên trong cùng mô hình mô phỏng.',
    'Không so sánh ARI từ Generator 3.0 với harm Candidate 4.1 như hai đầu của cùng mẫu. RQ3 tự có predicted partitions và đối chứng oracle trong Candidate. Harm là điểm thiệt hại latent do mô hình mô phỏng quy định, không phải số ca tử vong hay người cứu được quan sát. Nearest-first là baseline chi phí di chuyển, không phải chính sách cứu hộ đã được xác nhận.')

add('III · RQ3 · Kết quả mô tả','Nearest-first có trung bình thấp hơn',dispatch_chart(),
    'Trong ba điều kiện đã thử, nearest-first có harm và tỷ lệ trễ hạn trung bình thấp hơn revised và legacy.',
    'Các cột là trung bình trên 40 seeds trong từng resource scenario; không coi ba conditions thành ba mẫu độc lập. Hai panel có đơn vị và thang khác nhau, đều bắt đầu từ 0. Không có CI của từng scenario trên hình này, nên chỉ đọc mô tả. Kiểm định ghép theo seed nằm ở slide tiếp theo. Không diễn giải thành kết luận thực địa.',source='dispatch')

infer=[]
for comparator,label in [('legacy_priority','Legacy'),('nearest_first','Nearest-first')]:
    for metric,mlabel in [('latent_harm','Điểm harm'),('deadline_miss_rate','Trễ hạn')]:
        r=paired[comparator,metric];v=float(r['mean_difference_candidate_minus_comparator']);p=float(r['holm_adjusted_p_value'])
        vs=f'{v:+.2f}' if metric=='latent_harm' else f'{v*100:+.2f} đpt'
        ps=f'{p:.3f}' if p>=.001 else f'{p:.2e}'
        infer.append([f'Revised − {label}',mlabel,vs,ps])
add('III · RQ3 · Suy luận thống kê','Chưa xác lập lợi ích tổng quát của revised',table(['Tương phản','Metric','Δ thô','Holm p'],infer)+
    '<p class="caption">Δ = revised − baseline · cả hai metric càng thấp càng tốt · âm = cải thiện · đpt = điểm phần trăm.</p>',
    'So với legacy: chưa có khác biệt được xác lập. So với nearest-first: revised bất lợi trên cả hai metric.',
    'Số liệu từ CSV reanalysis cấp seed, 40 cặp. Đọc chênh lệch thô, không lấy cột mean định hướng lợi ích rồi đặt nhãn revised-minus-baseline. Deadline p trong CSV là khoảng 1.17e-6, trong paper prose khoảng 1.3e-6; slide giữ giá trị CSV và nguồn để kiểm tra. Kết luận về ý nghĩa không thay đổi. Không gọi không-significant là tương đương hoặc không có tác động.',source='paired')

add('IV · Thảo luận','Ba kết quả, ba phạm vi bằng chứng',table(['Tầng','Được hỗ trợ','Giới hạn được quan sát'],[
    ['<b>Gom cụm</b>','Chặn khoảng cách cạnh có điều kiện.','Chưa xác lập ưu thế Product; nhạy với GPS, thời gian và bản sao 5×.'],
    ['<b>Xếp hạng</b>','Bất biến bản sao chính xác khi nhóm và input cố định.','Đồng chỉnh benefit còn yếu; chiến dịch phối hợp vẫn làm lệch điểm.'],
    ['<b>Điều phối</b>','Định lượng được hệ quả trong mô hình và các cấu hình đã thử.','Revised chưa có lợi ích tổng quát; kết quả chưa kiểm chứng ngoài thực địa.'],
    ]),
    'Bảo đảm một tính chất cục bộ chưa đủ để suy ra chất lượng của toàn quy trình.',
    'Trở lại câu hỏi trung tâm. Không mô tả mọi kết quả âm là bằng chứng mô hình vô dụng; chúng chỉ bác bỏ hoặc chưa xác lập những ưu thế trong phạm vi đã kiểm tra. Các RQ dùng hai bộ riêng, nên bảng này là tổng hợp kết luận theo tầng, không phải một phép đo nhân quả từ đầu đến cuối.')

add('IV · Giới hạn & hướng kiểm chứng','Bước tiếp theo phải bổ sung bằng chứng',table(['Giới hạn hiện tại','Hướng kiểm chứng tiếp theo · chưa thực hiện'],[
    ['Báo cáo và nhãn được sinh.','Tiếp cận snapshot tin báo thật; xác minh vị trí cứu hộ; gán nhãn cùng/khác sự cố độc lập.'],
    ['Benefit và công thức ưu tiên chưa được chuyên gia xác nhận.','Xây rubric ưu tiên cùng chuyên gia; kiểm tra độ đồng thuận và đồng chỉnh ở mức sự cố.'],
    ['Harm, di chuyển và nguồn lực là giả định mô phỏng.','Đối chiếu nhật ký điều phối/tiếp cận; kiểm tra nhiều giả định và điều kiện nguồn lực.'],
    ['Chưa đo chuyển miền và thiếu dữ liệu RQ1.','Kiểm thử generator khác, sự kiện khác và missingness được khóa trước.'],
    ]),
    'Dữ liệu thực cần đúng ngữ nghĩa và đúng nhãn cho từng RQ; có dữ liệu thật chưa tự đủ để xác nhận cả ba.',
    'Slide trả lời trực tiếp câu hỏi tại sao cần Limits/Future work. Giới hạn dữ liệu đã trình ở đầu; cuối chỉ gắn từng giới hạn với phép kiểm chứng phù hợp. Đây là đề xuất tiếp theo, không phải kết quả đã chạy. Không hứa một kế hoạch đã có tài trợ, đối tác hay thời hạn. Có thể nhắc audit dữ liệu hiện hữu khi hỏi đáp, nhưng không đưa số liệu khảo sát mới vào kết quả bài báo.')

add('IV · Kết luận','Điều bài báo xác lập được',
    '<div class="conclusions"><div><span>01</span><p>Product gating cho <b>chặn cạnh có điều kiện</b>;<br>chưa xác lập ưu thế gom cụm.</p></div><div><span>02</span><p>Tổng hợp theo họ <b>bất biến với bản sao chính xác</b>;<br>chưa xác lập chất lượng ưu tiên tổng quát.</p></div><div><span>03</span><p><b>Điều phối cần được đánh giá riêng</b>;<br>kết luận hiện giới hạn trong mô phỏng.</p></div></div>',
    'Nghiên cứu làm rõ điều kiện áp dụng và giới hạn của từng tầng trước khi đưa ra tuyên bố ứng dụng.',
    'Kết thúc bằng ba câu trả lời cho RQ. Có thể nói: Chúng tôi chỉ ra rằng các bảo đảm ở một bước chưa chuyển thành lợi ích điều phối trong các mô phỏng đã thử; cần kiểm chứng độc lập bằng dữ liệu và đánh giá phù hợp trước khi mở rộng kết luận.')

add('Trao đổi với hội đồng','Cảm ơn hội đồng',
    '<p class="closing">Kính mời câu hỏi và góp ý.</p>'+pills('Dữ liệu & giá trị ngoại suy','Tính chất toán học','Thiết kế đối chứng','Kết quả RQ1–RQ3')+
    '<p class="caption">Phần sau gồm các slide dự phòng để giải thích phương pháp và bằng chứng.</p>',
    note='Dừng tại đây trong phần trình bày chính. Dùng O để mở mục lục; các slide dự phòng A1–A5 ở cuối. Không trình chiếu phụ lục tuần tự trừ khi hội đồng yêu cầu.',cls='thanks')

add('A1 · Dự phòng · Dữ liệu','Câu trả lời ngắn về dữ liệu tổng hợp',
    '<blockquote>“Chúng tôi dùng dữ liệu bán tổng hợp và tổng hợp để có nhãn cần thiết và kiểm soát từng nhiễu khi kiểm thử. Đổi lại, kết quả phụ thuộc cơ chế sinh, chưa phản ánh độ khó và lợi ích cứu hộ ngoài thực địa. Vì vậy bài chỉ kết luận trong phạm vi mô phỏng; bước tiếp theo là bổ sung dữ liệu thật và nhãn phù hợp từng RQ.”</blockquote>'+table(['RQ','Bằng chứng thực cần bổ sung'],[
    ['RQ1','Tin báo đủ vị trí/thời gian và nhãn cùng/khác sự cố.'],['RQ2','Nhãn ưu tiên hoặc benefit độc lập ở mức sự cố/cụm.'],['RQ3','Nguồn lực, hành trình, thời điểm tiếp cận và kết quả; nếu còn sinh thì vẫn là mô phỏng.']]),
    'Lý do chọn dữ liệu giải thích thiết kế; bất lợi giới hạn kết luận.',
    'Trả lời trong 30–45 giây rồi dừng để hội đồng hỏi sâu. Không nói không có dữ liệu thực ở bất kỳ đâu, không đồng nhất nhãn cần chú ý tin nhắn với benefit cứu hộ và không dùng dân số làm người mắc kẹt.',appendix=True)

add('A2 · Dự phòng · Định lý','Điều kiện của chặn không gian',grid(
    card('Product','Đặt B = β + γ > 0','<p>0 &lt; θ &lt; B:</p><div class="formula compact">d &lt; σ √[2 log(B / θ)]</div><p>θ ≥ B: tập cạnh giữ nghiêm ngặt rỗng.</p><p>θ ≤ 0: ngưỡng chưa cho cutoff hữu hạn.</p>'),
    card('Additive','Cần α > 0 và θ > B','<p>B &lt; θ &lt; B + α:</p><div class="formula compact">d &lt; σ √[2 log(α / (θ − B))]</div><p>θ ≤ B: nhìn chung chưa có chặn địa lý hữu hạn chỉ từ ngưỡng.</p>'))+
    '<p class="caption">Thành phần nhiều nút: D &lt; h rθ nếu hop diameter h hữu hạn đã quan sát; pipeline chưa kiểm soát h trước.</p>',
    'Chặn cạnh là tính chất hình học của trọng số và ngưỡng; chưa suy ra ARI tốt hơn.',
    'Bằng chứng: a_i a_j≤1 và T,C≤1, nên w×≤B exp(-d²/2σ²). Lấy θ<w× rồi log cho chặn. Với additive, θ<αG+B dẫn tới chặn chỉ khi θ>B. Quy tắc symmetrized top-k có thể làm degree vượt k.',appendix=True)

full_bench=[]
for key,name in [('additive_cij_louvain','Additive Louvain'),('product_cij_leiden','Product Leiden'),('convex_cij_louvain','Convex Louvain'),('product_cij_louvain','Product Louvain'),('additive_cij_louvain_matched_density','MD Additive'),('coordinate_kmeans','Coordinate K-means'),('spatial_agglomerative','Spatial agglomerative'),('hdbscan_all','HDBSCAN'),('geo_time_dbscan','Geo-time DBSCAN'),('dbscan_all','DBSCAN all features')]:
    r=benchmark[key];full_bench.append([name,f"{float(r['ari_mean']):.4f}",f"[{float(r['ari_ci95_low']):.4f}, {float(r['ari_ci95_high']):.4f}]",f"{float(r['pair_f1_mean']):.4f}"])
add('A3 · Dự phòng · RQ1','Đầy đủ baseline gom cụm',table(['Phương pháp','ARI','Bootstrap 95% CI','Pair F1'],full_bench,'dense'),
    'Matched-density giảm khác biệt mật độ cạnh, vẫn chưa cô lập tác động nhân quả của riêng toán tử.',
    'Đối chiếu paper Table 2 và benchmark_summary.csv. Product dùng q=.90, k=8, σ=700m; additive tinh chỉnh độc lập q=.95, k=8, σ=700m; cả hai resolution 1.2. Product−MD additive ARI≈+.00989, CI [-.00100,.02082], Holm p=.2560. Các CI riêng không thay kiểm định ghép.',source='benchmark',appendix=True)

add('A4 · Dự phòng · RQ2','Vai trò của các hằng số heuristic',grid(
    card('Confidence','Q = sigmoid(b₀ + b₁Iảnh + b₂ log(1+n))','<p>b₀ = −0,2 · b₁ = 1,4 · b₂ = 0,9.</p><p>n đếm payload gần nhau có định danh duy nhất.</p><p>Q là heuristic, chưa phải xác suất đúng đã hiệu chuẩn.</p>'),
    card('Priority','P = [1+(μ−1)tanh(V̄/s)] × W','<p>W = ωE Ē + ωF F̄ + ωN N̄.</p><p>ω = (0,34; 0,33; 0,33), μ = 2, s = 10.</p><p>Nref = 500 · Vcap = 50.</p>'))+
    '<p class="caption">Phân tích độ nhạy cục bộ: 21 cấu hình × 40 seeds = 840 quan sát; các khoảng biến thiên trung bình NDCG@5 được thử đều &lt; 0,01.</p>',
    'Ổn định cục bộ theo hằng số chưa xác nhận giá trị chính sách hoặc chất lượng xếp hạng.',
    'Các aggregation dùng confidence-gated family maxima; công thức rút gọn trên slide gọi W để đọc dễ, xem Eq.4 bản tiếng Anh để biết chuẩn hóa N và clipping N/V. Không suy Nref/Vcap không có tác dụng chỉ vì mean NDCG giữ nguyên ở mức đã báo cáo. Chưa có xác nhận chuyên gia cho các trọng số.',appendix=True)

add('A5 · Dự phòng · Suy luận & nguồn','Đọc đúng độ bất định và dấu hiệu ứng',grid(
    card('Đơn vị','40 cặp run/seed','<p>RQ1: 40 test runs; bootstrap 10.000 lần cho tương phản chuẩn.</p><p>RQ2/RQ3: bootstrap 5.000 lần.</p><p>RQ3 gộp ba điều kiện trong seed.</p>'),
    card('Kiểm định','Wilcoxon + Holm','<p>CI bootstrap chưa hiệu chỉnh và p Wilcoxon/Holm có thủ tục khác nhau.</p><p>Không có ý nghĩa thống kê chưa chứng minh tương đương.</p><p>Trung bình từng scenario là mô tả.</p>'),
    card('Dấu & nguồn','Δ = candidate − comparator','<p>Harm/trễ hạn: âm là tốt hơn.</p><p>ARI/NDCG: dương là tốt hơn.</p><p>CSV có thêm effect định hướng lợi ích; không trộn hai quy ước.</p>')),
    'Nguồn nội dung: paper/main.tex · số liệu biểu đồ: các CSV kết quả có manifest kèm bản trình bày.',
    'sources.json lưu đường dẫn, SHA-256 và rows biểu đồ. Đọc bibliography của bài nếu cần nguồn nghiên cứu trước. Bản HTML tự chứa font và đồ họa, không gửi dữ liệu hay phụ thuộc CDN. Deadline-miss Holm p trong CSV khoảng 1.1745e-6, prose bài khoảng 1.3e-6; chênh lệch đã ghi trong manifest.',appendix=True)


CSS='''
*{box-sizing:border-box} :root{--navy:#101B2D;--cream:#F7F6F1;--ink:#101B2D;--muted:#5A6270;--blue:#2B5FA8;--orange:#A3430F;--line:#D9DEE6}html,body{height:100%;margin:0}body{font-family:DeckSans,Lato,Arial,sans-serif;background:#0B1322;color:var(--ink);overflow:hidden}button,select{font:inherit}button,a,select{touch-action:manipulation}button:focus-visible,a:focus-visible,select:focus-visible{outline:3px solid #F0904F;outline-offset:4px}#viewport{position:fixed;inset:0}#stage{position:absolute;width:1600px;height:900px;transform-origin:top left}.slide{position:absolute;inset:0;padding:57px 80px 0;background:var(--cream);visibility:hidden;opacity:0;transition:opacity .18s}.slide.on{visibility:visible;opacity:1}.eyebrow{font-size:20px;letter-spacing:2.7px;font-weight:700;text-transform:uppercase;color:var(--orange);margin:0 0 14px}.slide h2{font-family:Georgia,'DejaVu Serif',serif;font-size:57px;line-height:1.15;font-weight:400;letter-spacing:-1.2px;margin:0 0 24px}.content{height:563px}.content>svg{display:block;width:100%;max-height:480px}.grid{display:grid;grid-auto-flow:column;grid-auto-columns:minmax(0,1fr);gap:28px}.card{border:1px solid var(--line);border-radius:17px;background:#FFF;padding:27px 30px;min-width:0}.card.blue{background:#EAF0F8}.tag{font-size:19px;letter-spacing:1.4px;text-transform:uppercase;font-weight:700;color:var(--orange);margin:0 0 20px}.card h3{font-size:32px;line-height:1.22;margin:0 0 20px;font-weight:700}.card p{font-size:26px;line-height:1.4;margin:14px 0;color:#3E4A5C}.metric{font-size:37px;color:var(--blue);font-weight:700;margin-top:32px}.metric span{color:var(--orange)}.number{font-size:64px;letter-spacing:-1px;color:var(--navy);font-weight:700;line-height:1.2;margin:16px 0}.number small{font-size:24px;letter-spacing:0;color:var(--muted);font-weight:400}.small-rule{height:1px;background:var(--line);margin:20px 0}.take{position:absolute;left:80px;right:80px;bottom:70px;min-height:80px;background:#DCE7F6;border:1px solid #B7CBE6;border-radius:15px;padding:18px 28px;display:flex;align-items:center;font-size:27px;line-height:1.35}.foot{position:absolute;left:80px;right:80px;bottom:23px;display:flex;justify-content:space-between;gap:15px;color:var(--muted);font-size:16px;line-height:1.25}.foot a{color:inherit;text-decoration:none}.foot .page{font-size:19px;white-space:nowrap}.pills{display:flex;gap:16px;flex-wrap:wrap;margin:22px 0}.pills span{background:#FFFFFF;border:1px solid var(--line);color:#3E4A5C;font-size:22px;border-radius:999px;padding:12px 23px}.caption{font-size:22px;color:var(--muted);line-height:1.4;margin:20px 0}.formula{font-family:Georgia,'DejaVu Serif',serif;font-size:36px;color:var(--blue);line-height:1.45;margin:25px 0}.formula.compact{font-size:29px}.equation-band{font-family:Georgia,'DejaVu Serif',serif;font-size:41px;text-align:center;padding:24px;background:#FFFFFF;border:1px solid var(--line);border-radius:17px;margin-bottom:8px}.split{display:grid;grid-template-columns:1fr 1fr 2fr;gap:10px;margin:4px 0 28px}.split>div{background:#DCE7F6;border-radius:13px;display:flex;gap:20px;align-items:center;padding:18px 25px}.split>div:last-child{background:var(--navy);color:#FFF}.split b{font-size:50px}.split span{font-size:25px}.statrow{display:flex;justify-content:space-between;gap:20px;padding:20px 0;font-size:23px;color:var(--muted)}.statrow b{color:var(--ink);padding-left:8px}table{width:100%;border-collapse:collapse;font-size:25px;line-height:1.3}th{text-align:left;padding:16px 20px;background:var(--navy);color:#FFFFFF;font-weight:700}th:first-child{border-radius:11px 0 0 0}th:last-child{border-radius:0 11px 0 0}td{border-bottom:1px solid var(--line);padding:22px 20px;vertical-align:top}tbody tr:nth-child(odd){background:#FFFFFF}td:first-child{width:33%}.dense{font-size:22px}.dense td{padding:9px 18px}.dense th{padding:12px 18px}.dense td:first-child{width:40%}.copyflow{display:flex;align-items:center;justify-content:space-between;gap:25px;margin:8px 0 28px}.copyflow>div:first-child{display:flex;gap:10px}.copy{font-size:24px;display:flex;align-items:center;justify-content:center;width:128px;height:90px;background:#FFFFFF;border:2px dashed #8FA0B8;border-radius:12px}.copyflow>b{font-size:46px;color:var(--orange)}.family{padding:20px 40px;font-size:31px;font-weight:700;text-align:center;border-radius:16px;background:#DCE7F6}.darkbox{background:var(--navy);color:#FFF}.conclusions{display:flex;flex-direction:column;gap:25px}.conclusions>div{display:flex;gap:35px;align-items:center;padding:22px 30px;border-bottom:1px solid var(--line)}.conclusions span{font-family:Georgia,serif;font-size:65px;color:var(--orange)}.conclusions p{font-size:31px;line-height:1.35;margin:0}.cover{background:var(--navy);color:var(--cream);padding-top:72px}.cover .eyebrow{color:#F0904F}.cover h2{font-size:71px;line-height:1.16;max-width:1000px;margin:35px 0 22px;color:#FFF}.cover .content{height:auto}.cover-sub{font-size:25px;line-height:1.5;color:#BFCBDD;max-width:1020px;margin:0}.cover-meta{display:flex;flex-direction:column;gap:10px;font-size:21px;border-left:3px solid #F0904F;padding-left:20px;position:absolute;left:80px;bottom:65px}.cover-meta span{color:#BFCBDD}.cover-art{position:absolute;width:570px;right:30px;bottom:58px;background:#F7F6F1;border-radius:14px;padding:18px}.cover-art svg{width:100%;height:auto}.cover .foot{color:#BFCBDD;font-size:13px;bottom:15px}.cover .foot .page{font-size:17px}.thanks h2{font-size:85px;margin-top:80px}.closing{font-size:38px;color:var(--muted);margin:40px 0 60px}.thanks .caption{margin-top:70px}blockquote{margin:0 0 25px;padding:25px 30px;border-left:5px solid var(--orange);background:#FFFFFF;font-size:29px;line-height:1.5}#toolbar{position:fixed;bottom:6px;left:50%;transform:translateX(-50%);display:flex;align-items:center;gap:6px;padding:6px 9px;border-radius:12px;background:#101B2DEE;color:#F7F6F1;z-index:10;box-shadow:0 3px 15px #0005;opacity:0.2;transition:opacity .15s}#toolbar:hover,#toolbar:focus-within,body.show-ui #toolbar{opacity:1}#toolbar button,#toolbar select{background:#1B2B47;border:1px solid #52647F;color:#F7F6F1;border-radius:7px;padding:6px 10px;font-size:13px;cursor:pointer}#toolbar select{width:190px}#counter{font-size:13px;min-width:56px;text-align:center}#progress{position:fixed;left:0;bottom:0;height:3px;background:#F0904F;z-index:12}#notes{position:fixed;right:20px;top:20px;bottom:65px;width:min(520px,90vw);overflow:auto;z-index:20;background:#FFF;border-radius:16px;padding:30px;box-shadow:0 5px 40px #0008;font-size:20px;line-height:1.6}#notes h3{font-size:25px;line-height:1.3}#notes button{float:right;padding:6px 12px;cursor:pointer}#overview{position:fixed;inset:20px;background:#F7F6F1;z-index:30;padding:30px;overflow:auto;border-radius:20px}#overview h2{font-size:28px}#overview .items{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:16px}#overview button{background:#FFF;color:var(--ink);border:1px solid var(--line);padding:20px;border-radius:12px;text-align:left;cursor:pointer;font-size:17px;line-height:1.4}#overview button b{display:block;color:var(--orange);font-size:21px;margin-bottom:10px}#overview button.current{outline:3px solid var(--blue)}#overview .close{float:right}#help{position:fixed;inset:20% 20%;z-index:40;background:#FFFFFF;border-radius:20px;padding:35px;font-size:22px;line-height:1.8;overflow:auto}.slide[hidden],#notes[hidden],#overview[hidden],#help[hidden]{display:none!important}.speaker-note{display:none}svg text{font-family:DeckSans,Lato,Arial,sans-serif}#live{position:absolute;width:1px;height:1px;clip-path:inset(50%);overflow:hidden}@media(prefers-reduced-motion:reduce){*{transition:none!important;scroll-behavior:auto!important}}@page{size:1600px 900px;margin:0}@media print{html,body{height:auto;background:#FFF;overflow:visible}#viewport{position:static}#stage{position:static;transform:none!important;width:1600px;height:auto}.slide,.slide[hidden]{position:relative!important;visibility:visible!important;opacity:1!important;display:block!important;width:1600px;height:900px;break-after:page;page-break-after:always;overflow:hidden}.slide:last-child{break-after:auto;page-break-after:auto}#toolbar,#progress,#notes,#overview,#help,#live{display:none!important}*{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
'''

font_css=''
for weight,filename in [(400,'Lato-Regular.ttf'),(700,'Lato-Bold.ttf')]:
    font=Path('/usr/share/fonts/truetype/lato')/filename
    font_css+=f'@font-face{{font-family:DeckSans;font-style:normal;font-weight:{weight};src:url(data:font/ttf;base64,{base64.b64encode(font.read_bytes()).decode()}) format("truetype");font-display:block}}'

main_count=sum(not s['appendix'] for s in slides)
sections=[]
for i,s in enumerate(slides):
    num=f'A{i-main_count+1}' if s['appendix'] else f'{i+1:02d}'
    source_path=SOURCES[s['source']]
    source_label=source_path if len(source_path)<92 else source_path.rsplit('/',1)[-1]
    footer=f'<div class="foot"><a href="../../{esc(source_path)}" title="{esc(source_path)}">Nguồn: {esc(source_label)}</a><span class="page">{num} · {"Dự phòng" if s["appendix"] else str(main_count)+" slide chính"}</span></div>'
    sections.append(f'<section class="slide {s["cls"]}{" on" if i==0 else ""}" id="s{i+1}" data-number="{num}" data-title="{esc(s["title"].replace("<br>"," "))}" data-appendix="{str(s["appendix"]).lower()}" aria-label="{num}: {esc(s["title"].replace("<br>"," "))}" aria-hidden="{str(i!=0).lower()}"><p class="eyebrow">{s["section"]}</p><h2>{s["title"]}</h2><div class="content">{s["body"]}</div>'+ (f'<div class="take">{s["take"]}</div>' if s['take'] else '')+footer+f'<aside class="speaker-note">{esc(s["note"])}</aside></section>')

JS='''
(()=>{'use strict';const slides=[...document.querySelectorAll('.slide')],stage=document.querySelector('#stage'),sel=document.querySelector('#jump'),notes=document.querySelector('#notes'),overview=document.querySelector('#overview');let current=0,lastFocus=null;const clamp=n=>Math.max(0,Math.min(slides.length-1,n));
function fit(){const w=innerWidth,h=innerHeight,k=Math.min(w/1600,h/900);stage.style.transform=`translate(${(w-1600*k)/2}px,${(h-900*k)/2}px) scale(${k})`;}
function go(n,hash=true){current=clamp(n);slides.forEach((s,i)=>{s.classList.toggle('on',i===current);s.setAttribute('aria-hidden',String(i!==current));s.inert=i!==current;});const s=slides[current];document.querySelector('#counter').textContent=`${current+1} / ${slides.length}`;sel.value=String(current);document.querySelector('#progress').style.width=`${(current+1)/slides.length*100}%`;document.querySelector('#live').textContent=s.dataset.number+': '+s.dataset.title;document.querySelector('#noteTitle').textContent=s.dataset.title;document.querySelector('#noteText').textContent=s.querySelector('.speaker-note').textContent;document.querySelector('#noteSource').textContent=s.querySelector('.foot a').title;document.querySelectorAll('#overview .items button').forEach((b,i)=>b.classList.toggle('current',i===current));if(hash)history.replaceState(null,'','#'+(current+1));}
slides.forEach((s,i)=>{let op=document.createElement('option');op.value=i;op.textContent=s.dataset.number+' · '+s.dataset.title;sel.appendChild(op);let b=document.createElement('button');b.innerHTML='<b>'+s.dataset.number+'</b>'+s.dataset.title;b.onclick=()=>{toggle(overview,false);go(i);};document.querySelector('#overview .items').appendChild(b);});
function toggle(el,value){const show=value===undefined?el.hidden:value;if(show){lastFocus=document.activeElement;el.hidden=false;el.querySelector('button')?.focus();}else{el.hidden=true;lastFocus?.focus();}}
document.querySelector('#prev').onclick=()=>go(current-1);document.querySelector('#next').onclick=()=>go(current+1);sel.onchange=()=>go(Number(sel.value));document.querySelector('#notesBtn').onclick=()=>toggle(notes);document.querySelector('#closeNotes').onclick=()=>toggle(notes,false);document.querySelector('#overviewBtn').onclick=()=>toggle(overview);document.querySelector('#closeOverview').onclick=()=>toggle(overview,false);document.querySelector('#helpBtn').onclick=()=>toggle(document.querySelector('#help'));document.querySelector('#closeHelp').onclick=()=>toggle(document.querySelector('#help'),false);document.querySelector('#printBtn').onclick=()=>window.print();
async function fs(){try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen();}catch(e){document.querySelector('#live').textContent='Không mở được toàn màn hình; dùng F11 của trình duyệt.';}}
document.querySelector('#fullBtn').onclick=fs;document.addEventListener('keydown',e=>{if(/SELECT|INPUT|TEXTAREA/.test(e.target.tagName))return;if(e.key==='Escape'){[notes,overview,document.querySelector('#help')].forEach(el=>{if(!el.hidden)toggle(el,false);});return;}if(!overview.hidden||!document.querySelector('#help').hidden)return;if(['ArrowRight','PageDown',' '].includes(e.key)){e.preventDefault();go(current+1);}else if(['ArrowLeft','PageUp'].includes(e.key)){e.preventDefault();go(current-1);}else if(e.key==='Home')go(0);else if(e.key==='End')go(slides.length-1);else if(e.key.toLowerCase()==='f')fs();else if(e.key.toLowerCase()==='n')toggle(notes);else if(e.key.toLowerCase()==='o')toggle(overview);else if(e.key==='?')toggle(document.querySelector('#help'));});
document.addEventListener('keydown',e=>{const modal=[overview,document.querySelector('#help')].find(el=>!el.hidden);if(modal&&e.key==='Tab'){const bs=[...modal.querySelectorAll('button')];const first=bs[0],last=bs.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}});
let tx=null;document.querySelector('#viewport').addEventListener('touchstart',e=>{tx=e.touches[0].clientX;},{passive:true});document.querySelector('#viewport').addEventListener('touchend',e=>{if(tx!==null){const dx=e.changedTouches[0].clientX-tx;if(Math.abs(dx)>60)go(current+(dx<0?1:-1));}tx=null;},{passive:true});let timer;document.addEventListener('pointermove',()=>{document.body.classList.add('show-ui');clearTimeout(timer);timer=setTimeout(()=>document.body.classList.remove('show-ui'),1800);});window.addEventListener('resize',fit);window.addEventListener('hashchange',()=>{const h=Number(location.hash.slice(1));if(Number.isInteger(h)&&h>0)go(h-1,false);});window.deck={go,slides,count:slides.length,mainCount:slides.filter(s=>s.dataset.appendix==='false').length};fit();let h=Number(location.hash.slice(1));go(Number.isInteger(h)&&h>0?h-1:0,false);document.fonts.ready.then(fit);
})();
'''

doc='<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Bảo vệ bài báo về gom cụm và xếp hạng tin báo cứu hộ lũ lụt; phân biệt dữ liệu bán tổng hợp, tổng hợp và giới hạn bằng chứng."><title>Bảo vệ bài báo · Flood-Rescue Reports · v1</title><style>'+font_css+CSS+'</style></head><body><div id="viewport"><main id="stage">'+''.join(sections)+'</main></div><nav id="toolbar" aria-label="Điều khiển trình chiếu"><button id="prev" aria-label="Slide trước">←</button><span id="counter"></span><button id="next" aria-label="Slide sau">→</button><select id="jump" aria-label="Chọn slide"></select><button id="overviewBtn">Mục lục · O</button><button id="notesBtn">Ghi chú · N</button><button id="fullBtn">Toàn màn hình · F</button><button id="printBtn">In / PDF</button><button id="helpBtn" aria-label="Hướng dẫn phím tắt">?</button></nav><div id="progress"></div><aside id="notes" hidden aria-label="Ghi chú thuyết trình"><button id="closeNotes" aria-label="Đóng ghi chú">Đóng</button><h3 id="noteTitle"></h3><p id="noteText"></p><small id="noteSource"></small></aside><div id="overview" hidden role="dialog" aria-modal="true" aria-label="Mục lục slide"><button class="close" id="closeOverview">Đóng · Esc</button><h2>Mục lục · '+str(main_count)+' slide chính + '+str(len(slides)-main_count)+' dự phòng</h2><div class="items"></div></div><div id="help" hidden role="dialog" aria-modal="true" aria-label="Hướng dẫn"><button id="closeHelp">Đóng · Esc</button><p>← / → · Page Up / Down · Space: chuyển slide<br>Home / End: đầu / cuối<br>O: mục lục · N: ghi chú · F: toàn màn hình<br>Vuốt trái/phải trên điện thoại<br>In / PDF: xuất toàn bộ slide, gồm dự phòng.</p><p>Bấm nền không chuyển slide. Phím Esc đóng bảng đang mở.</p></div><div id="live" role="status" aria-live="polite"></div><script>'+JS+'</script></body></html>'
(HERE/'index.html').write_text(doc,encoding='utf-8')

chart_data={
    'rq1_benchmark':bc,
    'rq1_stress':[dict(method=k[0],scenario=k[1],ari=v) for k,v in stress.items()],
    'rq2_alignment':al,
    'rq2_drift':[dict(scenario=k[0],method=k[1],n=len(v),mean=statistics.mean(v)) for k,v in robust.items()],
    'rq3_means':[dict(scenario=k[0],policy=k[1],metric=k[2],n=len(v),mean=statistics.mean(v)) for k,v in dispatch.items()],
    'rq3_tests':[{k:r[k] for k in ['comparator','metric','mean_difference_candidate_minus_comparator','holm_adjusted_p_value','n_seed_pairs']} for r in paired.values()],
}
manifest={
    'version':'v1','date':'2026-10-30','language':'vi','main_slides':main_count,'appendix_slides':len(slides)-main_count,
    'scope':'Presentation of existing research; no manuscript edits, new experiments or publication.',
    'sources':{k:{'path':v,'sha256':hashlib.sha256((ROOT/v).read_bytes()).hexdigest()} for k,v in SOURCES.items()},
    'visual_reference':'User-supplied PLM + MCNN HTML: navy/cream, restrained blue/orange, diagrams, takeaway strips. New layout/code; no embedded reference images reused.',
    'fonts':[{'name':'Lato','license':'SIL Open Font License 1.1','local_license':'FONT-LICENSE.txt','source':'/usr/share/fonts/truetype/lato','embedded':True}],
    'notes':['Paper Results is the narrative authority; numerical charts read existing CSVs.','Deadline-miss revised-vs-nearest Holm p is 1.174528414e-6 in seed CSV, approximately 1.3e-6 in paper prose. Slide 19 uses CSV.','Raw delta is candidate minus comparator, not the benefit-oriented effect column.','Data-choice explanations are methodological rationales supported by the design, not claims about unrecorded historical author decisions.','No assertion that no real dataset exists globally. The named resources in the paper do not jointly provide all RQ labels.'],
    'charts':chart_data,
}
(HERE/'sources.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(HERE/'FONT-LICENSE.txt').write_text(Path('/usr/share/doc/fonts-lato/copyright').read_text(),encoding='utf-8')
script=['# Ghi chú thuyết trình · Bản 01\n','Giả định thời lượng: khoảng 20–25 phút, chưa gồm hỏi đáp. Phần chính dừng ở slide 23.\n']
for i,s in enumerate(slides):
    num=f'A{i-main_count+1}' if s['appendix'] else str(i+1)
    script.append(f'## {num}. {s["title"].replace("<br>"," ")}\n\n{s["note"]}\n\nNguồn: `{SOURCES[s["source"]]}`\n')
(HERE/'speaker-notes.md').write_text('\n'.join(script),encoding='utf-8')
print(json.dumps({'main':main_count,'appendix':len(slides)-main_count,'bytes':len(doc.encode()),'output':str(HERE/'index.html')},ensure_ascii=False))
