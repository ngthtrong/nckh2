#!/usr/bin/env python3
"""Readability repairs: monochrome ERD/UML/flowcharts; no product writes."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import textwrap
import xml.etree.ElementTree as ET

from matplotlib.patches import Ellipse
import build_system_diagrams as base
from build_detailed_system_diagrams import Diagram as CheckedDiagram, schema, W

ROOT=base.ROOT
REVIEW=ROOT/"diagram-revisions/2026-10-25-full-figure-audit"


@contextmanager
def black_lines():
    old=base.LINE
    base.LINE="#111111"
    try:yield
    finally:base.LINE=old


class Diagram(CheckedDiagram):
    def text(self,*args,**kwargs):
        kwargs.setdefault("color","#111111")
        return super().text(*args,**kwargs)
    def shape(self,*args,**kwargs):
        kwargs["line"]="#111111"
        if kwargs.get("kind") not in ["white","gray"]:kwargs["kind"]="white"
        return super().shape(*args,**kwargs)
    def arrow(self,*args,**kwargs):
        with black_lines():return super().arrow(*args,**kwargs)


def ellipse(d,x,y,w,h,text,*,size=10,fill='white'):
    identifier=d.ident("ellipse")
    d.ax.add_patch(Ellipse((x+w/2,y+h/2),w,h,facecolor=fill,edgecolor="#111111",lw=.9,zorder=2))
    c=ET.SubElement(d.cells,"mxCell",id=identifier,parent="1",vertex="1",style=f"ellipse;fillColor={fill};strokeColor=#111111;")
    ET.SubElement(c,"mxGeometry",x=str(x),y=str(y),width=str(w),height=str(h),**{"as":"geometry"})
    d.shapes[identifier]=(x,y,w,h,False)
    if text:d.text(x+w/2,y+h/2,text,size=size,bounds=(x+12,y+4,w-24,h-8))
    return identifier


def node(d,x,y,w,h,text,*,diamond=False,size=10):
    n=d.shape(x,y,w,h,kind="white",diamond=diamond)
    d.text(x+w/2,y+h/2,text,size=size,bounds=(x+7,y+4,w-14,h-8))
    return n


def cap(d,p,q,kind):
    import numpy as np
    p=np.array(p,dtype=float);q=np.array(q,dtype=float)
    v=(q-p)/np.linalg.norm(q-p);normal=np.array([-v[1],v[0]])
    def bar(at):
        c=p+v*at;d.arrow([tuple(c-normal*4),tuple(c+normal*4)],heads=False)
    if kind=="one":bar(4);bar(10)
    elif kind in ["optional","many"]:
        c=p+v*14
        ellipse(d,c[0]-2.5,c[1]-2.5,5,5,"",size=9)
        if kind=="optional":bar(5)
        else:
            d.arrow([tuple(p+normal*4),tuple(p+v*8),tuple(p-normal*4)],heads=False)
    else:raise ValueError(kind)


def relation(d,pts,left,right,source,target,label=None,at=None):
    d.arrow(pts,heads=False,dashed=True,source=source,target=target,label=label,at=at)
    cap(d,pts[0],pts[1],left);cap(d,pts[-1],pts[-2],right)


def erd():
    d=Diagram("database_erd",427,"ERD Crow's Foot — bảy thực thể lưu trữ",width=W)
    data=schema();d.schema_data=data
    pos={"reports":(10,27,255),"messages_dedup":(292,27,205),"report_events":(292,221,205),
         "operators":(524,27,194),"sessions":(524,201,194),"teams":(524,291,194),"server_meta":(10,359,255)}
    uq={"operators":{"username","display_name"},"teams":{"name"}}
    refs={"reports":{"assigned_team_id"},"report_events":{"report_id"},"sessions":{"operator_id"}}
    d.text(10,10,"ERD · CROW'S FOOT · TOÀN BỘ THUỘC TÍNH TRONG DDL",ha="left",bold=True,size=10)
    ids={}
    for name,(x,y,w) in pos.items():
        cols=data[name]["columns"];h=21+11.4*len(cols)
        ids[name]=d.shape(x,y,w,h,rounded=False,kind="white")
        d.text(x+8,y+10,name,ha="left",bold=True,size=10.2)
        d.arrow([(x,y+20),(x+w,y+20)],heads=False)
        for i,c in enumerate(cols):
            tags=[]
            if c['pk']:tags.append('PK')
            if c['name'] in refs.get(name,set()):tags.append('REF')
            if c['notnull']:tags.append('NN')
            if c['name'] in uq.get(name,set()):tags.append('UQ/CI' if name=='operators' else 'UQ')
            if c['default'] is not None:tags.append('='+str(c['default']))
            value=f"{c['name']} {c['type']}"+(' '+','.join(tags) if tags else '')
            d.text(x+6,y+28+11.4*i,value,ha="left",size=9,bounds=(x+3,y+20,w-6,h-20))
    relation(d,[(265,246),(292,246)],'one','many',ids['reports'],ids['report_events'])
    relation(d,[(621,162),(621,201)],'optional','many',ids['operators'],ids['sessions'])
    relation(d,[(265,330),(280,330),(280,378),(524,378)],'many','optional',ids['reports'],ids['teams'],
             label='assigned_team_id → teams.id',at=(389,365))
    d.shape(292,174,205,18,rounded=False,kind="white")
    d.text(299,183,"UQ (client_id, sequence_number)",ha="left",size=9)
    d.text(292,207,"Không có cột FK từ dedup tới reports.",ha="left",size=9)
    d.text(292,401,"PK: khóa chính; NN: NOT NULL; UQ: UNIQUE; CI: NOCASE.",ha="left",size=9)
    d.text(10,411,"REF: tham chiếu logic; DDL chưa khai báo FOREIGN KEY. Nét đứt: quan hệ không định danh (PK con độc lập).",ha="left",size=9)
    d.text(10,422,"Ký hiệu đầu nối: || một; o| không hoặc một; o< không hoặc nhiều. operator_id giữ nullability của DDL.",ha="left",size=9)
    return d


def actor(d,x,y,text):
    ellipse(d,x-6,y,12,12,"",size=9)
    d.arrow([(x,y+12),(x,y+36)],heads=False)
    d.arrow([(x-12,y+23),(x+12,y+23)],heads=False)
    d.arrow([(x-12,y+51),(x,y+36),(x+12,y+51)],heads=False)
    d.text(x,y+66,text,size=9.5)
    return (x,y+23)


def uml_link(d,pts,kind=None,label_at=None):
    assert len(pts)==2, 'UML use case connectors must be direct straight segments'
    d.arrow(pts,heads=bool(kind),dashed=bool(kind))
    cell=list(d.cells)[-1]
    cell.set('style',cell.get('style')+'edgeStyle=none;curved=0;orthogonalLoop=0;')
    if kind:
        cell.set('style',cell.get('style')+'endArrow=open;endFill=0;')
        d.text(*label_at,'«'+kind+'»',size=9.2,label=True)


def direct_case(d,source,target,kind=None,label_at=None):
    x,y,w,h,_=d.shapes[target];center=(x+w/2,y+h/2)
    if isinstance(source,str):
        a,b,u,v,_=d.shapes[source];origin=(a+u/2,b+v/2)
        start=(a+u if center[0]>origin[0] else a,origin[1])
    else:origin=source;start=source
    # Attach at the left/right extreme of each ellipse. The straight fan stays
    # outside the column, so it cannot cut through neighbouring use case text.
    finish=(x if origin[0]<center[0] else x+w,center[1])
    uml_link(d,[start,finish],kind,label_at)
    if not hasattr(d,'usecase_links'):d.usecase_links=[]
    d.usecase_links.append({'source':source,'target':target,'kind':kind or 'association',
                            'points':[start,finish]})


def usecase_mobile():
    d=Diagram('usecase_mobile',423,'Use case UML — ứng dụng di động',width=W)
    d.shape(110,20,515,371,rounded=False,kind='white')
    d.text(122,36,'ỨNG DỤNG DI ĐỘNG FLUTTER',ha='left',bold=True,size=11)
    values=['UC-M01 · Gửi SOS khẩn cấp','UC-M02 · Tạo báo cáo chi tiết','UC-M05 · Tra cứu trạng thái',
            'UC-M08 · Chỉnh sửa thông tin','UC-M06 · Hướng dẫn / sơ cứu','UC-M07 · Danh bạ khẩn cấp']
    ids=[ellipse(d,145,60+r*55,210,42,text,size=9.8) for r,text in enumerate(values)]
    sms=ellipse(d,430,60,185,42,'UC-M03 · Gửi SMS\ndự phòng')
    ai=ellipse(d,430,143,185,42,'UC-M04 · Nhận diện\nmức ngập từ ảnh')
    actor(d,53,196,'Người dân /\nđội cứu hộ')
    for n in ids:direct_case(d,(65,219),n)
    actor(d,678,60,'SMS gateway\n«actor»');direct_case(d,(666,83),sms)
    direct_case(d,sms,ids[0],'extend',(390,65))
    direct_case(d,sms,ids[1],'extend',(389,113))
    direct_case(d,ai,ids[1],'extend',(389,177))
    d.text(10,404,'SMS: khi gửi data chưa thành công và đủ điều kiện. Nhận diện ảnh: khi có ảnh và AI sẵn sàng.',ha='left',size=9)
    d.text(10,418,'Actor ngoài ranh giới hệ thống; association là đoạn thẳng không mũi tên; «extend» hướng về use case cơ sở.',ha='left',size=9)
    return d


def usecase_dashboard():
    d=Diagram('usecase_dashboard',420,'Use case UML — dashboard điều phối',width=W)
    d.shape(125,20,540,370,rounded=False,kind='white')
    d.text(137,36,'DASHBOARD ĐIỀU PHỐI VÀ API NGHIỆP VỤ',ha='left',bold=True,size=11)
    values=['UC-W01 · Đăng nhập','UC-W02 · Giám sát bản đồ / ưu tiên','UC-W04 · Quản lý danh sách báo cáo',
            'UC-W06 · Tiếp nhận báo cáo tổng đài','UC-W08 · Phân công đội cứu hộ',
            'UC-W09 · Cập nhật trạng thái cứu hộ','UC-W10 · Xuất CSV / GeoJSON']
    ids=[ellipse(d,160,60+r*44,260,34,value,size=9.8) for r,value in enumerate(values)]
    cluster=ellipse(d,470,95,175,42,'UC-W03 · Lấy kết quả\nphân cụm và ưu tiên')
    loc=ellipse(d,470,169,175,42,'UC-W05 · Bổ sung\ntọa độ thủ công')
    sms=ellipse(d,470,243,175,42,'UC-W07 · Nhận SMS\nqua gateway')
    actor(d,53,180,'Điều phối viên')
    for n in ids:direct_case(d,(65,203),n)
    actor(d,697,218,'SMS\ngateway\n«actor»');direct_case(d,(685,241),sms)
    direct_case(d,ids[1],cluster,'include',(446,94))
    direct_case(d,loc,ids[2],'extend',(446,210))
    d.text(10,402,'Bổ sung tọa độ là mở rộng khi cần xác minh vị trí. Phiên đăng nhập là tiền điều kiện của thao tác được bảo vệ.',ha='left',size=9)
    d.text(10,414,'«include»: từ ca cơ sở tới phần dùng chung; «extend»: từ phần mở rộng về ca được mở rộng (UML 2.5.1 §18.1.4).',ha='left',size=9)
    return d


def usecase_overall():
    d=Diagram('usecase',410,'Use case UML — toàn hệ thống cứu hộ',width=W)
    d.shape(100,20,230,365,rounded=False,kind='white')
    d.shape(406,20,252,365,rounded=False,kind='white')
    d.text(112,36,'ỨNG DỤNG DI ĐỘNG',ha='left',bold=True,size=11)
    d.text(418,36,'ĐIỀU PHỐI / TIẾP NHẬN',ha='left',bold=True,size=11)
    mobile=['UC-01 · Gửi SOS','UC-02 · Tạo báo cáo chi tiết','UC-03 · SMS dự phòng',
            'UC-04 · Nhận diện ảnh ngập','UC-05 · Tra cứu trạng thái']
    web=['UC-06 · Đăng nhập','UC-07 · Quản lý báo cáo','UC-08 · Giám sát bản đồ / ưu tiên',
         'UC-09 · Kết quả phân cụm / ưu tiên','UC-10 · Tiếp nhận tổng đài','UC-12 · Nhận SMS gateway',
         'UC-11 · Phân công đội cứu hộ','UC-13 · Cập nhật trạng thái','UC-14 · Bổ sung tọa độ',
         'UC-15 · Xuất CSV / GeoJSON']
    m=[ellipse(d,120,69+r*62,190,43,v,size=9.5) for r,v in enumerate(mobile)]
    w=[ellipse(d,416,59+r*31,232,27,v,size=9.3) for r,v in enumerate(web)]
    actor(d,45,190,'Người dân /\nđội cứu hộ')
    for n in m:direct_case(d,(57,213),n)
    actor(d,697,192,'Điều phối\nviên')
    for i,n in enumerate(w):
        if i!=5:direct_case(d,(685,215),n)
    actor(d,365,190,'SMS gateway\n«actor»')
    direct_case(d,(353,213),m[2]);direct_case(d,(377,213),w[5])
    d.text(10,400,'Hai phân hệ là hai subject UML; actor nằm ngoài từng ranh giới. Use case chi tiết giữ quan hệ «include»/«extend».',ha='left',size=9)
    return d


def gridflow(name,title,headings,specs,edges,footer=''):
    d=Diagram(name,417,title,width=W)
    for c,heading in enumerate(headings):
        d.shape(10+c*244,10,220,384,rounded=False,kind='white',background=True)
        d.text(20+c*244,28,heading,ha='left',bold=True,size=10.5)
    nodes={};geometry={}
    for key,(c,r,text,decision) in specs.items():
        x=20+c*244;y=52+r*68;w=200;h=51
        if decision:x+=15;w-=30
        nodes[key]=node(d,x,y,w,h,text,diamond=decision,size=9.5)
        geometry[key]=(x,y,w,h,c,r)
    for edge in edges:
        source,target,label=edge[:3]
        x,y,w,h,c,r=geometry[source];a,b,u,v,k,s=geometry[target]
        if c==k and s==r+1:pts=[(x+w/2,y+h),(a+u/2,b)]
        elif c==k:
            gutter=14+c*244 if s<r else 226+c*244
            pts=[(x if s<r else x+w,y+h/2),(gutter,y+h/2),(gutter,b+v/2),(a if s<r else a+u,b+v/2)]
        elif k==c+1:
            gutter=242+c*244
            pts=[(x+w,y+h/2),(gutter,y+h/2),(gutter,b+v/2),(a,b+v/2)]
        else:
            pts=[(x+w,y+h/2),(242+c*244,y+h/2),(242+c*244,390),(W-5,390),(W-5,b+v/2),(a+u,b+v/2)]
        d.arrow(pts,source=nodes[source],target=nodes[target])
        if label:
            if c==k and s==r+1:at=(x+w/2+32,y+h+8)
            elif k==c+1:at=(242+c*244,(y+h/2+b+v/2)/2)
            elif c==k and s>r:at=(a+u/2,b-9)
            elif c==k:at=(a+u-30,b+v+8)
            else:at=(x+w/2,y-8)
            if len(edge)>3:at=edge[3]
            d.text(*at,label,size=9,label=True)
    if footer:d.text(10,408,footer,ha='left',size=9)
    return d


def tracking():
    return gridflow('flow_04_track_rescue_status','Theo dõi và đồng bộ trạng thái',['1 · ĐỌC TRẠNG THÁI','2 · LƯU VÀ HIỂN THỊ','3 · LẶP CÓ ĐIỀU KIỆN'],{
        'open':(0,0,'Mở màn hình theo dõi\nLấy các report ID cần tra cứu',False),
        'net':(0,1,'Có mạng?',True),
        'local':(0,2,'Không: đọc trạng thái đã lưu\ntrong Hive; không tạo ca mới',False),
        'api':(0,3,'Có: GET /api/reports/status\nGửi danh sách ids',False),
        'merge':(1,0,'Ghép kết quả theo report ID\nChỉ nhận trạng thái đi tiến',False),
        'states':(1,1,'processing: đã tiếp nhận\ndispatched: đã điều phối\nresolved: hoàn tất\ncancelled: đã đóng',False),
        'ui':(1,3,'Lưu Hive; cập nhật timeline\nThông báo trạng thái nghiệp vụ',False),
        'active':(2,0,'Còn ca chưa kết thúc\nvà app ở foreground?',True),
        'timer':(2,2,'Có mạng: đặt lịch tra cứu\n15 s khi theo dõi / mặc định 60 s',False),
        'stop':(2,4,'Ca cuối / app ngừng theo dõi:\ndừng hoặc đổi lịch phù hợp',False)},
        [('open','net',''),('net','local','Không'),('net','api','Có'),('local','merge',''),('api','merge',''),('merge','states',''),('states','ui',''),('ui','active',''),('active','timer','Có'),('active','stop','Không')],
        'Trạng thái gửi/ACK và trạng thái cứu hộ là hai lớp thông tin khác nhau; polling không xác nhận đội đã đến hiện trường.')


def compose():
    return gridflow('flow_02_create_report_edge_ai','Tạo báo cáo chi tiết và suy luận ảnh',['1 · ẢNH / AI TÙY CHỌN','2 · THÔNG TIN HIỆN TRƯỜNG','3 · LƯU VÀ GỬI'],{
        'open':(0,0,'Mở biểu mẫu báo cáo\nCó thể chọn hoặc chụp ảnh',False),
        'photo':(0,1,'Có ảnh và AI\nđã sẵn sàng?',True),
        'infer':(0,2,'AnalyzeImageUseCase\nMobileNetV3-Large, ONNX/PTE\nNhãn ngập + confidence',False),
        'fallback':(0,4,'Không có ảnh / AI lỗi:\ngiữ thông tin nhập tay\nKhông gán nhãn non_flood giả',False),
        'form':(1,0,'Nhập số mắc kẹt, bị thương\nNhóm yếu thế; mô tả; liên hệ',False),
        'lr':(1,1,'Năm dấu hiệu khẩn cấp\nLR khi sẵn sàng → điểm E_i',False),
        'gps':(1,2,'Lấy GPS hoặc nhập vị trí\nKhông lấy được: để trống\nKhông gán tọa độ mặc định',False),
        'check':(1,4,'Kiểm tra dữ liệu nhập\nBảo toàn ảnh cục bộ',False),
        'record':(2,0,'Tạo RescueRecord, report ID\nstatus=processing; synced=false',False),
        'queue':(2,1,'Ghi bản ghi + Outbox\nĐịnh danh message/hash/sequence',False),
        'send':(2,3,'deliverRecord\nGửi thích ứng; ACK metadata\nẢnh có thể đồng bộ sau',False),
        'done':(2,4,'Hiển thị kết quả gửi\nChưa ACK: giữ hàng đợi/retry',False)},
        [('open','photo',''),('photo','infer','Có'),('photo','fallback','Không'),('infer','form',''),('fallback','form',''),('form','lr',''),('lr','gps',''),('gps','check',''),('check','record',''),('record','queue',''),('queue','send',''),('send','done','')],
        'Ảnh và AI hỗ trợ khai báo; dữ liệu thiếu được giữ rõ ràng. E_i được gửi nhưng adapter hiện chưa đọc trực tiếp trường này.')


def adaptive():
    return gridflow('flow_03_adaptive_network_send','Truyền tải thích ứng, ACK và hoàn tất ảnh',['1 · METADATA / OUTBOX','2 · CHÍNH SÁCH ẢNH','3 · KẾT QUẢ VÀ RETRY'],{
        'save':(0,0,'Lưu bản ghi và xếp Outbox\nGiữ report ID; JCS + hash',False),
        'data':(0,1,'Có data?',True),
        'sms':(0,2,'Không: thử SMS nếu đủ điều kiện\nVẫn giữ Outbox chờ HTTP',False),
        'meta':(0,3,'Có: POST /sync/messages\nACK nối theo message_id',False),
        'ack':(0,4,'accepted / duplicate:\nmetadataSynced=true\nXóa message đã ACK',False),
        'image':(1,0,'Còn ảnh phải gửi?',True),
        'probe':(1,1,'Nếu có ảnh: đo /probe\n64 KiB; ngân sách 6 s\nĐánh giá lại khi đồng bộ muộn',False),
        'modes':(1,2,'≥1000 kbit/s: ảnh gốc\nConfidence ≥0,90: có thể chỉ text\n50–<1000: ảnh nén\n<50 nhưng có data: chỉ text',False),
        'upload':(1,3,'Ảnh gốc / ảnh nén JPEG q=60\nNén: cạnh ngắn 1024; giữ tỷ lệ\nPOST /api/reports multipart',False),
        'finish':(1,4,'Ảnh đã có / chế độ chỉ text:\nhoàn tất synced=true',False),
        'retry':(2,0,'Metadata / ảnh lỗi tạm:\nTimeout / 408 / 429 / 5xx\nretry_later: backoff + jitter\nGiữ nguyên ID và hash',False),
        'reject':(2,2,'rejected không retry:\nlưu dead-letter / syncError\nKhông xóa dấu vết lỗi',False),
        'status':(2,4,'GET /api/reports/status\nTheo dõi trạng thái cứu hộ\nĐộc lập trạng thái gửi ảnh',False)},
        [('save','data',''),('data','sms','Không'),('data','meta','Có',(236,168)),('sms','meta','Có data lại'),('meta','ack',''),('ack','image',''),('image','probe','Có'),('image','finish','Không',(474,300)),('probe','modes',''),('modes','upload','Ảnh'),('modes','finish','Chỉ text',(474,247)),('upload','finish',''),('finish','status',''),('upload','retry','Lỗi tạm'),('meta','reject','rejected',(680,390))],
        'SMS đã được hệ điều hành gửi không có nghĩa gateway/backend đã nhận. ACK metadata không đồng nghĩa ảnh đã gửi xong.')


def training():
    return gridflow('flow_09_ai_training_optimization','Huấn luyện, tối ưu và xuất runtime',['1 · DỮ LIỆU / KIẾN TRÚC','2 · HUẤN LUYỆN / VALIDATION','3 · TEST / CÁC NHÁNH TỐI ƯU'],{
        'data':(0,0,'1702 ảnh, bốn mức ngập\nTrain 1189 / val 257 / test 256',False),
        'prep':(0,1,'EXIF → RGB → letterbox 256²\nBilinear; chuẩn hóa ImageNet\nTrain: flip / affine / jitter',False),
        'model':(0,3,'MobileNetV3-Large\nDropout 0,25; Linear 4 lớp',False),
        'freeze':(1,0,'Khóa backbone ba epoch đầu\nFeatures ở eval; huấn luyện head',False),
        'tune':(1,1,'Mở backbone, AdamW\nCE smoothing + 0,1 severity\nReduceLROnPlateau',False),
        'val':(1,2,'Validation mỗi epoch\nAccuracy / lỗi nặng\nEarly stopping patience 7',False),
        'ckpt':(1,4,'Chọn checkpoint trên validation\nƯu tiên accuracy; có tie-break\nbằng tỷ lệ lỗi nặng',False),
        'test':(2,0,'Đánh giá test độc lập\nFP32: accuracy / F1 / lỗi nặng\nKhông dùng test chọn checkpoint',False),
        'branches':(2,1,'Các nhánh riêng:\nPTQ calibration trên train; QAT\nCắt tỉa kênh có cấu trúc',False),
        'export':(2,3,'Xuất ONNX và ExecuTorch/PTE\nGiữ tiền xử lý, thứ tự lớp\nĐối chiếu manifest / hash / parity',False),
        'mobile':(2,4,'Tích hợp Flutter\nĐánh giá runtime / thiết bị\nGiữ provenance từng seed',False)},
        [('data','prep',''),('prep','model',''),('model','freeze',''),('freeze','tune',''),('tune','val',''),('val','tune','Còn epoch'),('val','ckpt','Chọn'),('ckpt','test',''),('test','branches',''),('branches','export',''),('export','mobile','')],
        'PTQ, QAT và pruning không phải các bước nén nối tiếp bắt buộc. Không gộp kết quả khác seed/runtime thành một phiên đo.')


def clustering():
    return gridflow('flow_06_clustering_priority','Cache, đồ thị Louvain và ưu tiên có chặn',['1 · CACHE VÀ ĐẦU VÀO','2 · ĐỒ THỊ VÀ CỘNG ĐỒNG','3 · HỌ BẰNG CHỨNG / ƯU TIÊN'],{
        'request':(0,0,'GET /api/clusters\nĐọc version epoch:cluster_rev',False),
        'snapshot':(0,1,'Không đổi: dùng snapshot\nChậm: trả stale + tính nền\nIf-None-Match khớp → 304',False),
        'active':(0,3,'Đọc active_only\nBỏ resolved và cancelled\nto_report_v2: L,T,F,E,N,V',False),
        'eligible':(0,4,'Đủ vị trí và thời gian?',True),
        'review':(1,0,'Thiếu L/T: hàng xem xét\nKhông suy tọa độ mặc định',False),
        'weights':(1,1,'Đủ: ma trận tương đồng\nHaversine / thời gian / ngữ cảnh\nProduct C_ij và độ tin cậy',False),
        'sparse':(1,2,'Ngưỡng quantile, top-K\nĐối xứng hợp các cạnh',False),
        'louvain':(1,4,'Louvain: cộng đồng đồ thị\nclusterKey = ID nhỏ nhất\nKhóa có thể đổi khi thành viên đổi',False),
        'families':(2,0,'Nhóm họ bằng chứng\nFingerprint / envelope\nQ_i và các tổng hợp có chặn',False),
        'score':(2,1,'Tổng hợp Ē, F̄, N̄, V̄\nƯu tiên có hệ số nhóm yếu thế\nSắp xếp giảm dần P(c)',False),
        'cache':(2,3,'Lưu snapshot RAM và ETag\nTrả clusters + review\ncomputedAt và stale',False),
        'view':(2,4,'Dashboard hỗ trợ quyết định\nCụm không thay report ID nghiệp vụ',False)},
        [('request','snapshot',''),('snapshot','active','Tính lại'),('active','eligible',''),('eligible','review','Thiếu'),('eligible','weights','Đủ'),('weights','sparse',''),('sparse','louvain',''),('louvain','families',''),('families','score',''),('score','cache',''),('review','cache',''),('cache','view','')],
        'P(c) = (wE·Ē + wF·F̄ + wN·N̄) × [1 + (μ−1)tanh(V̄/s)]; không thay bằng tổng tuyến tính bốn đại lượng.')


def deployment():
    d=Diagram('deployment_infrastructure',405,'Triển khai Docker Compose',width=W)
    host=d.shape(225,20,335,330,rounded=False,kind='white')
    d.text(235,35,'«device» HOST DOCKER COMPOSE',ha='left',bold=True,size=11)
    be=node(d,244,69,295,62,'«container» be · FastAPI / Uvicorn\nrescue_core; Louvain và ưu tiên\nMặc định :8000 → container :8000')
    dash=node(d,244,163,139,60,'«container» dashboard\nNginx · HTML/JS/Leaflet\n:8080 → :80')
    fe=node(d,400,163,139,60,'«container» fe\nNginx · Flutter Web\n:8081 → :80')
    vol=node(d,244,267,295,65,'«volume» be-data → /var/lib/rescue\nSQLite WAL: rescue_reports.db\nẢnh: uploads/; backup: backups/')
    phone=node(d,10,70,177,62,'«device» Android\nGPS, Camera, Hive\nONNX / ExecuTorch tại biên')
    dispatcher=node(d,10,174,177,60,'«device» máy điều phối\nTrình duyệt Web GIS\nHTTP :8080')
    browser=node(d,10,278,177,60,'«device» trình duyệt thử\nỨng dụng Flutter Web\nHTTP :8081')
    gateway=node(d,584,70,134,62,'«external system»\nSMS gateway\n/api/sms/inbound')
    d.arrow([(187,101),(244,101)],source=phone,target=be,label='HTTP',at=(215,86))
    d.arrow([(187,204),(244,193)],source=dispatcher,target=dash)
    d.arrow([(187,308),(211,308),(211,236),(470,236),(470,223)],source=browser,target=fe)
    d.arrow([(584,101),(539,101)],source=gateway,target=be)
    d.arrow([(313,163),(313,131)],source=dash,target=be)
    d.arrow([(470,163),(470,131)],source=fe,target=be)
    d.text(390,147,'Proxy API → be:8000',size=9,label=True)
    d.arrow([(392,131),(392,251),(392,267)],source=be,target=vol)
    d.text(10,381,'Cổng là giá trị mặc định, có thể cấu hình qua biến môi trường. Volume giữ dữ liệu khi container được tạo lại.',ha='left',size=9.5)
    d.text(10,398,'SMS cần gateway token; điện thoại thật phải truy cập được backend. Không đồng nhất Flutter Web với suy luận native Android.',ha='left',size=9)
    return d


def status_machine():
    d=Diagram('status_machine',245,'Máy trạng thái nghiệp vụ cứu hộ',width=base.WIDTH)
    p=node(d,20,55,108,45,'processing\nđã tiếp nhận',size=10)
    a=node(d,174,55,108,45,'dispatched\nđã điều phối',size=10)
    r=node(d,328,55,108,45,'resolved\nhoàn tất',size=10)
    c=node(d,174,157,108,45,'cancelled\nđã đóng',size=10)
    ellipse(d,2,72,8,8,'',size=9,fill='#111111')
    d.arrow([(10,76),(20,76)],target=p)
    d.arrow([(128,76),(174,76)],source=p,target=a,label='PATCH',at=(151,62))
    d.arrow([(282,76),(328,76)],source=a,target=r,label='PATCH',at=(305,62))
    d.arrow([(74,100),(74,179),(174,179)],source=p,target=c,label='đóng + lý do',at=(115,166))
    d.arrow([(228,100),(228,157)],source=a,target=c,label='đóng + lý do',at=(268,129))
    for x,y in [(445,76),(306,179)]:
        ellipse(d,x-5,y-5,10,10,'',size=9);ellipse(d,x-2.5,y-2.5,5,5,'',size=9,fill='#111111')
    d.arrow([(436,76),(440,76)],source=r)
    d.arrow([(282,179),(301,179)],source=c)
    d.text(10,223,'Trạng thái cuối không đổi sang trạng thái khác; statusVersion tăng.',ha='left',size=9)
    d.text(10,237,'Giao đội là thao tác riêng; đường vẽ thể hiện tiến trình thông thường.',ha='left',size=9)
    return d


def research_pipeline():
    base.PALE['purple']='#F0E6F6'
    d=CheckedDiagram('research_pipeline_report',385,'Ranh giới suy luận và đánh giá',width=W)
    d.shape(10,10,708,177,rounded=False,kind='blue',background=True)
    d.shape(10,211,708,155,rounded=False,kind='purple',background=True)
    d.text(20,27,'OBSERVABLE PIPELINE · KHÔNG DÙNG NHÃN THẬT',ha='left',bold=True,size=11)
    values=['Báo cáo\nhiện trường','Đủ vị trí\nvà thời gian?','Masked similarity\ngraph thưa\nngưỡng + k-NN','Phân cụm\ndự đoán','Họ bản sao\nxếp hạng\ncó chặn','Lập lịch theo\ncụm dự đoán']
    ids=[]
    for i,value in enumerate(values):
        x=22+i*115;n=d.shape(x,60,101,60,kind='white',diamond=i==1);ids.append(n)
        d.text(x+50.5,90,value,size=9.5,bounds=(x+6,65,89,50))
        if i:d.arrow([(x-14,90),(x,90)],source=ids[i-1],target=n)
    rev=d.shape(137,145,140,28,kind='amber');d.text(207,159,'Thiếu L/T: review',size=10)
    d.arrow([(187,120),(187,145)],source=ids[1],target=rev)
    d.text(20,238,'EVALUATOR-ONLY\nTruth chỉ nối sau khi\nđầu ra đã khóa',ha='left',bold=True,size=10)
    evaluators=[]
    for x,value in [(265,'RQ1 · phân cụm\npartition đã khóa + truth'),(445,'RQ2 · xếp hạng\noracle groups + benefit'),(625,'RQ3 · điều phối\nschedule đã khóa + truth')]:
        evaluators.append(d.shape(x-81,252,162,44,kind='white'));d.text(x,274,value,size=9.5)
    # RQ2 is evaluated with oracle groups, independently of inferred clusters.
    # Only the locked RQ1 partition and RQ3 schedule cross this boundary.
    for src,source_x,target_x,level,target in [(ids[3],417.5,265,198,evaluators[0]),
                                             (ids[5],647.5,625,204,evaluators[2])]:
        d.arrow([(source_x,120),(source_x,level),(target_x,level),(target_x,252)],
                source=src,target=target,dashed=True)
    d.text(445,329,'Evaluator truth: incident ID; N_true, V_true; deadline;\nservice demand; harm và independent benefit',size=10)
    for x in [265,445,625]:d.arrow([(x,307),(x,296)],dashed=True)
    d.text(10,380,'Màu và ranh giới giữ concept gốc: suy luận quan sát; review fail-closed; đánh giá độc lập không rò rỉ truth.',ha='left',size=9)
    return d


def main():
    REVIEW.mkdir(parents=True,exist_ok=True)
    results={};errors=[];combined=ET.Element('mxfile',host='app.diagrams.net')
    for factory in [erd,usecase_overall,usecase_mobile,usecase_dashboard,tracking,compose,deployment,adaptive,status_machine,training,clustering,research_pipeline]:
        d=factory()
        try:results[d.name]=d.save(ROOT/'assets/diagrams',REVIEW/'previews')
        except ValueError as exc:errors.append(str(exc));continue
        legacy_preview=ROOT/'assets/diagrams'/f'{d.name}_preview.png'
        if legacy_preview.exists():legacy_preview.write_bytes((REVIEW/'previews'/f'{d.name}.png').read_bytes())
        if hasattr(d,'usecase_links'):
            results[d.name]['uml_links']=d.usecase_links
            results[d.name]['direct_straight_links']='PASS'
        if hasattr(d,'schema_data'):
            results[d.name]['schema']=d.schema_data
            results[d.name]['table_count']=len(d.schema_data)
            results[d.name]['column_count']=sum(len(v['columns']) for v in d.schema_data.values())
        combined.append(d.mx.find('diagram'));print(d.name,'PASS')
    if errors:raise SystemExit('\n'.join(errors))
    ET.indent(combined);ET.ElementTree(combined).write(REVIEW/'readable-diagrams.drawio',encoding='utf-8',xml_declaration=True)
    (REVIEW/'diagram-validation.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n')
    sources=['report/scripts/build_readable_report_diagrams.py','report/scripts/build_system_diagrams.py',
             'report/scripts/build_detailed_system_diagrams.py','products/be/storage.py']
    (REVIEW/'diagram-sources.json').write_text(json.dumps({s:hashlib.sha256((ROOT.parent/s).read_bytes()).hexdigest()
                                                        for s in sources},indent=2)+'\n')


if __name__=='__main__':main()
