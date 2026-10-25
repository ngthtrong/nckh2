#!/usr/bin/env python3
"""Six detailed, source-backed A4-landscape system figures.

Uses the existing vector/Draw.io renderer. Icons are original vector drawings,
not screenshots or external licensed assets. Schema comes from literal DDL
parsed into an in-memory SQLite database; application modules are not imported.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import xml.etree.ElementTree as ET

from matplotlib.patches import Circle, Ellipse

from build_system_diagrams import Diagram as BaseDiagram, INK, LINE, PALE, ROOT

W = 257 / 25.4 * 72
REVIEW = ROOT / "diagram-revisions/2026-10-25-six-system-diagrams"
BLUE = "#276487"
GREEN = "#237A67"
ORANGE = "#A76A22"
RED = "#AA4D48"


class Diagram(BaseDiagram):
    def text(self, *args, **kwargs):
        artist=super().text(*args, **kwargs)
        artist.set_linespacing(1.15)
        return artist

    def save(self, output, preview):
        self.fig.canvas.draw()
        renderer=self.fig.canvas.get_renderer()
        boxes=[]
        for artist,_,_ in self.texts:
            box=artist.get_window_extent(renderer).transformed(self.ax.transData.inverted())
            boxes.append((artist.get_text(),min(box.x0,box.x1),min(box.y0,box.y1),
                          max(box.x0,box.x1),max(box.y0,box.y1)))
        overlaps=[]
        for i,(a,x1,y1,x2,y2) in enumerate(boxes):
            for b,u1,v1,u2,v2 in boxes[i+1:]:
                if min(x2,u2)-max(x1,u1)>.4 and min(y2,v2)-max(y1,v1)>.4:
                    overlaps.append(f"{a!r} overlaps {b!r}")
        if overlaps:raise ValueError(self.name+"\n"+"\n".join(overlaps))
        result=super().save(output,preview)
        result["text_overlaps"]="PASS"
        return result


def circle(d, x, y, r, *, fill="white", stroke=LINE):
    d.ax.add_patch(Circle((x,y),r,facecolor=fill,edgecolor=stroke,lw=.9,zorder=2.8))
    cell=ET.SubElement(d.cells,"mxCell",id=d.ident("circle"),parent="1",vertex="1",
                       style=f"ellipse;fillColor={fill};strokeColor={stroke};strokeWidth=0.9;")
    ET.SubElement(cell,"mxGeometry",x=str(x-r),y=str(y-r),width=str(r*2),height=str(r*2),**{"as":"geometry"})


def icon(d, name, x, y, size=18):
    """Draw a small semantic glyph, including native editable Draw.io paths."""
    s=size/20
    def line(points):
        d.arrow([(x+a*s,y+b*s) for a,b in points],heads=False)
    def ring(a,b,r):circle(d,x+a*s,y+b*s,r*s)
    if name=="phone":
        d.shape(x+3*s,y,14*s,20*s,kind="white")
        line([(7,3),(13,3)]);line([(7,17),(13,17)])
    elif name=="screen":
        d.shape(x,y,20*s,14*s,kind="white",rounded=False)
        line([(10,14),(10,19)]);line([(5,19),(15,19)])
    elif name=="database":
        d.shape(x+1*s,y+3*s,18*s,14*s,kind="white",rounded=False)
        for h in [3,10,17]:
            d.ax.add_patch(Ellipse((x+10*s,y+h*s),18*s,6*s,facecolor="white",edgecolor=LINE,lw=.9,zorder=4))
            cell=ET.SubElement(d.cells,"mxCell",id=d.ident("ellipse"),parent="1",vertex="1",
                               style=f"ellipse;fillColor=#FFFFFF;strokeColor={LINE};")
            ET.SubElement(cell,"mxGeometry",x=str(x+s),y=str(y+(h-3)*s),width=str(18*s),height=str(6*s),**{"as":"geometry"})
    elif name=="pin":
        ring(10,7,6);line([(5,11),(10,20),(15,11)]);ring(10,7,2)
    elif name=="camera":
        d.shape(x,y+5*s,20*s,13*s,kind="white",rounded=False)
        line([(4,5),(6,1),(13,1),(15,5)]);ring(10,11,4)
    elif name=="graph":
        pts=[(3,4),(16,3),(8,12),(18,18),(1,18)]
        for a,b in [(0,1),(0,2),(1,2),(2,3),(2,4)]:line([pts[a],pts[b]])
        for a,b in pts:ring(a,b,2.2)
    elif name=="shield":
        line([(10,0),(19,4),(17,13),(10,20),(3,13),(1,4),(10,0)])
        line([(5,9),(9,13),(15,6)])
    elif name=="team":
        for a,b in [(5,5),(15,5),(10,11)]:ring(a,b,3)
        line([(0,17),(0,12),(4,9)]);line([(20,17),(20,12),(16,9)])
        line([(4,20),(4,17),(10,14),(16,17),(16,20)])
    elif name=="chip":
        d.shape(x+4*s,y+4*s,12*s,12*s,kind="white",rounded=False)
        for a in [6,10,14]:
            line([(a,0),(a,4)]);line([(a,16),(a,20)])
            line([(0,a),(4,a)]);line([(16,a),(20,a)])
    elif name=="sms":
        line([(0,2),(20,2),(20,15),(9,15),(3,20),(3,15),(0,15),(0,2)])
        for a in [5,10,15]:ring(a,8,.7)
    elif name=="layers":
        for h in [0,6,12]:line([(0,h+4),(10,h),(20,h+4),(10,h+8),(0,h+4)])
    elif name=="clock":
        ring(10,10,9);line([(10,4),(10,10),(15,13)])
    elif name=="document":
        line([(3,0),(13,0),(18,5),(18,20),(3,20),(3,0)])
        for h in [8,12,16]:line([(6,h),(15,h)])
    else:
        raise ValueError(name)


def section(d,x,y,w,h,title,*,glyph="layers",kind="gray"):
    node=d.shape(x,y,w,h,kind=kind,background=True)
    icon(d,glyph,x+10,y+8,16)
    d.text(x+34,y+16,title,ha="left",bold=True,size=10,
           bounds=(x+31,y+3,w-36,25))
    return node


def step(d,x,y,w,h,value,*,kind="white",diamond=False,size=9.2):
    node=d.shape(x,y,w,h,kind=kind,diamond=diamond)
    d.text(x+w/2,y+h/2,value,size=size,bounds=(x+6,y+4,w-12,h-8))
    return node


def lines(d,x,y,values,*,width,leading=13,size=9.2):
    for i,value in enumerate(values):
        d.text(x,y+i*leading,value,ha="left",size=size,
               bounds=(x-1,y-7,width+2,leading*len(values)+13))


def heading(d,x,y,value,glyph="document"):
    icon(d,glyph,x,y-8,15)
    d.text(x+23,y,value,ha="left",bold=True,size=9.7)


def schematic_map(d,x,y,w,h):
    d.shape(x,y,w,h,kind="white",rounded=False)
    for pts in [[(0,.35),(.3,.4),(.65,.2),(1,.3)],[(.3,0),(.43,.5),(.3,1)],
                [(0,.8),(.55,.65),(1,.8)],[(.7,0),(.6,.5),(.85,1)]]:
        d.arrow([(x+a*w,y+b*h) for a,b in pts],heads=False)
    for a,b in [(.24,.28),(.7,.55),(.58,.69)]:icon(d,"pin",x+a*w,y+b*h,10)
    d.text(x+w/2,y+h-7,"Bản đồ minh họa",size=9,label=True)


def architecture():
    d=Diagram("functional_architecture",415,"2.1 · Kiến trúc chức năng và các tuyến dữ liệu",width=W)
    section(d,10,10,210,333,"DI ĐỘNG BIÊN",glyph="phone",kind="blue")
    section(d,249,10,230,333,"BACKEND TRUNG TÂM",glyph="shield",kind="teal")
    section(d,508,10,210,333,"WEB ĐIỀU PHỐI",glyph="screen",kind="amber")
    d.text(23,43,"Người dân / đội cứu hộ",ha="left",size=9.2)
    d.text(521,43,"Điều phối viên",ha="left",size=9.2)
    icon(d,"phone",24,52,45);icon(d,"camera",90,54,23);icon(d,"pin",142,54,23)
    d.text(46,76,"SOS",size=9,bold=True,color=RED)
    lines(d,82,91,["SOS một chạm / báo cáo", "Ảnh, GPS, N, V, mô tả"],width=127)
    d.text(23,116,"N: số người; V: nhóm yếu thế",ha="left",size=9.2)
    heading(d,23,130,"AI tại thiết bị","chip")
    lines(d,23,151,["MobileNetV3-Large: bốn mức ngập", "Confidence; ONNX / ExecuTorch", "LR: 5 dấu hiệu → E_i"],width=190,leading=13)
    heading(d,23,194,"Hive + Outbox","database")
    lines(d,23,216,["Report ID; message ID; client / sequence", "Payload JCS → SHA-256; ACK / retry", "Metadata và ảnh có trạng thái gửi riêng"],width=190)
    heading(d,23,269,"Truyền tải thích ứng","sms")
    lines(d,23,290,["Ảnh gốc / ảnh nén / chỉ metadata", "SMS dự phòng; giữ hàng đợi HTTP", "Tra cứu /api/reports/status"],width=190)
    api=step(d,261,65,206,70,"FastAPI · tiếp nhận và xác thực\nPOST /sync/messages · JSON batch\nPOST /api/reports · metadata + ảnh\nSMS webhook / nhập tổng đài",kind="white")
    icon(d,"graph",269,166,32)
    lines(d,309,166,["ClusterService + rescue_core", "Louvain; ưu tiên P(c)", "Thiếu L/T → hàng xem xét", "clusterKey; cache RAM"],width=160,leading=14)
    d.text(364,239,"epoch:cluster_rev · snapshot ETag\nKhông đổi: cache; chậm: stale + tính nền",size=9.1)
    icon(d,"database",265,275,42)
    lines(d,321,280,["SQLite WAL + uploads/", "reports, teams, auth, events", "messages_dedup; server_meta"],width=146,leading=15)
    d.arrow([(364,135),(364,155)],source=api)
    d.arrow([(364,252),(364,264),(286,264),(286,275)],label="Đọc active reports",at=(410,265))
    d.arrow([(261,123),(254,123),(254,296),(265,296)],double=True,source=api)
    schematic_map(d,523,52,180,91)
    d.text(613,155,"Leaflet GIS · cụm theo P(c)",size=9.4,bold=True)
    heading(d,521,187,"Xem xét và xác minh","pin")
    lines(d,521,208,["Ảnh, nhãn AI, số nạn nhân", "Hàng thiếu vị trí; bổ sung tọa độ", "Polling 5 s: changes / clusters"],width=184)
    heading(d,521,264,"Điều phối và truy vết","team")
    lines(d,521,285,["Giao đội; cập nhật trạng thái riêng", "report_events; CSV / GeoJSON", "Tài khoản; sao lưu; quản trị"],width=184)
    d.arrow([(220,103),(261,103)],double=True,label="[1]",at=(238,91),target=api)
    d.arrow([(467,103),(508,103)],double=True,label="[3]",at=(488,91),source=api)
    gateway=step(d,104,352,185,23,"SMS gateway → webhook",kind="gray")
    icon(d,"sms",78,353,19)
    d.arrow([(117,343),(117,348),(104,348),(104,363)],dashed=True,target=gateway)
    d.arrow([(289,363),(297,363),(297,348),(240,348),(240,127),(261,127)],dashed=True,source=gateway,target=api,
            label="[2]",at=(238,151))
    d.text(10,389,"[1] HTTP: metadata/ảnh, ACK và trạng thái. [2] GSM SMS → gateway → /api/sms/inbound.",ha="left",size=9)
    d.text(10,404,"[3] API điều phối, JSON/ETag. App gửi E_i; adapter lấy E từ urgency hoặc mô tả.",ha="left",size=9)
    return d


def overview():
    d=Diagram("flowchart",405,"2.2 · Phối hợp bốn phân hệ và vòng phản hồi",width=W)
    for x,title,glyph,kind in [(10,"1 · THIẾT BỊ","phone","blue"),(190,"2 · TIẾP NHẬN","shield","teal"),
                                (370,"3 · PHÂN CỤM","graph","teal"),(550,"4 · ĐIỀU PHỐI","screen","amber")]:
        section(d,x,10,168,381,title,glyph=glyph,kind=kind)
    create=step(d,20,51,148,53,"SOS / báo cáo chi tiết\nẢnh và AI là tùy chọn\nGPS có thể thiếu; N, V\nLưu bản ghi → Outbox")
    send=step(d,20,125,148,53,"JCS; hash; ID / sequence\nẢnh gốc / nén / metadata\nKhông data: thử SMS\nChưa gửi: giữ queue, retry")
    ack=step(d,35,205,118,44,"HTTP đã\nACK?",kind="amber",diamond=True)
    attachment=step(d,20,275,148,40,"ACK metadata; còn chờ ảnh\nGửi xong mới synced=true")
    appstatus=step(d,20,340,148,40,"GET /api/reports/status\nHiển thị; chưa cuối: tra tiếp")
    entry=step(d,200,76,148,53,"JSON sync / Multipart /\nSMS gateway / tổng đài\nKiểm tra riêng từng kênh\nHeader / token / quyền gộp")
    save=step(d,200,156,148,60,"Message ID/hash; client/seq\nhoặc report ID + chủ sở hữu\nSQLite: reports, dedup, ảnh\nACK theo message/request")
    updates=step(d,200,281,148,64,"Ghi report_events: actor/giờ\nĐổi dữ liệu → cluster_rev\nCa cuối ra khỏi active\nAPI trả trạng thái cho app")
    cache=step(d,380,51,148,70,"GET /api/clusters\nCache: epoch:cluster_rev\nKhông đổi: dùng snapshot\nChậm: stale + tính nền\nETag khớp client → 304")
    complete=step(d,389,151,130,45,"Đủ vị trí\nvà thời gian?",kind="amber",diamond=True)
    review=step(d,380,216,148,34,"Thiếu L/T:\nhàng xem xét riêng")
    compute=step(d,380,273,148,60,"to_report_v2: F,E,N,V\nHaversine; time; nội dung\nMa trận đồ thị → Louvain\nP(c); clusterKey; JSON/ETag")
    icon(d,"graph",392,350,27)
    d.text(476,364,"Họ bằng chứng\nTổng hợp có chặn",size=9.2)
    schematic_map(d,560,51,148,55)
    d.text(634,120,"Đăng nhập; polling mỗi 5 s",size=9.1)
    inspect=step(d,560,150,148,59,"Cụm ưu tiên / hàng xem xét\nẢnh, AI, số nạn nhân\nXác minh; bổ sung vị trí\nChọn ca theo report ID")
    assign=step(d,560,234,148,43,"PUT /team: giao đội\nPATCH /status: dispatched")
    field=step(d,560,302,148,32,"Tác nghiệp thực địa\nngoài phần mềm",kind="gray")
    closed=step(d,560,354,148,32,"resolved / cancelled\nĐóng ca kèm lý do")
    d.arrow([(94,104),(94,125)],source=create,target=send)
    d.arrow([(168,150),(181,150),(181,102),(200,102)],source=send,target=entry)
    d.arrow([(274,129),(274,156)],source=entry,target=save)
    d.arrow([(200,192),(183,192),(183,227),(153,227)],source=save,target=ack)
    d.arrow([(35,227),(15,227),(15,152),(20,152)],source=ack,target=send,dashed=True)
    d.text(48,191,"Chưa: retry",size=9,label=True)
    d.arrow([(94,249),(94,275)],source=ack,target=attachment,label="Có",at=(110,263))
    d.arrow([(94,315),(94,340)],source=attachment,target=appstatus)
    d.arrow([(348,186),(362,186),(362,88),(380,88)],dashed=True,source=save,target=cache)
    d.arrow([(560,87),(545,87),(545,80),(528,80)],source=None,target=cache)
    d.arrow([(454,121),(454,151)],source=cache,target=complete)
    d.arrow([(389,173),(375,173),(375,233),(380,233)],source=complete,target=review)
    d.text(401,205,"Thiếu",size=9,label=True)
    d.arrow([(454,196),(535,196),(535,303),(528,303)],source=complete,target=compute)
    d.text(514,206,"Đủ",size=9,label=True)
    d.arrow([(528,233),(543,233),(543,180),(560,180)],source=review,target=inspect)
    d.arrow([(528,303),(543,303),(543,233)],source=compute,heads=False)
    d.arrow([(634,209),(634,234)],source=inspect,target=assign)
    d.arrow([(634,277),(634,302)],source=assign,target=field)
    d.arrow([(634,334),(634,354)],source=field,target=closed)
    d.arrow([(560,255),(360,255),(360,294),(348,294)],source=assign,target=updates)
    d.arrow([(560,371),(546,371),(546,348),(359,348),(359,330),(348,330)],source=closed,target=updates)
    d.arrow([(200,315),(180,315),(180,360),(168,360)],source=updates,target=appstatus)
    d.text(10,400,"Nét đứt: retry hoặc dữ liệu thay đổi. SMS đã gửi không đồng nghĩa backend đã nhận; ACK không xác nhận đã cứu.",ha="left",size=9)
    return d


def schema():
    tree=ast.parse((ROOT.parent/"products/be/storage.py").read_text())
    conn=sqlite3.connect(":memory:")
    for node in ast.walk(tree):
        if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Attribute) or node.func.attr!="execute" or not node.args:
            continue
        arg=node.args[0]
        if isinstance(arg,ast.Constant) and isinstance(arg.value,str):sql=arg.value
        elif isinstance(arg,ast.JoinedStr):
            sql="".join(part.value if isinstance(part,ast.Constant) else "reports" for part in arg.values)
        else:continue
        if re.match(r"\s*CREATE (?:TABLE|UNIQUE INDEX)",sql,re.I):
            conn.execute(sql)
    names=["reports","messages_dedup","report_events","operators","sessions","teams","server_meta"]
    result={}
    for name in names:
        result[name]={"columns":[dict(zip(["cid","name","type","notnull","default","pk"],row))
                                 for row in conn.execute(f"PRAGMA table_info({name})")],
                      "foreign_keys":list(conn.execute(f"PRAGMA foreign_key_list({name})"))}
    result["messages_dedup"]["unique_pair"]=[r[2] for r in conn.execute("PRAGMA index_info(idx_client_seq)")]
    assert result["messages_dedup"]["unique_pair"]==["client_id","sequence_number"]
    assert all(not v["foreign_keys"] for v in result.values())
    conn.close()
    return result


def erd():
    d=Diagram("database_erd",418,"2.5 · Lược đồ đầy đủ và các liên hệ logic của backend",width=W)
    data=schema();d.schema_data=data
    # Every column in the actual DDL is represented exactly once.
    coordinates={"reports":(10,27,255),"messages_dedup":(292,27,205),
                 "report_events":(292,221,205),"operators":(524,27,194),
                 "sessions":(524,194,194),"teams":(524,285,194),"server_meta":(10,359,255)}
    unique={"operators":{"username","display_name"},"teams":{"name"}}
    d.text(10,10,"SCHEMA SQLITE · TẤT CẢ CỘT TRONG DDL",ha="left",bold=True,size=10)
    nodes={}
    for name,(x,y,w) in coordinates.items():
        cols=data[name]["columns"];h=21+11.4*len(cols)
        nodes[name]=d.shape(x,y,w,h,kind="white",rounded=False)
        d.shape(x,y,w,20,kind="blue" if name in ["reports","report_events"] else "gray",rounded=False,background=True)
        icon(d,"database" if name=="reports" else "document",x+6,y+3,13)
        d.text(x+25,y+10,name,ha="left",bold=True,size=9.8)
        for i,c in enumerate(cols):
            tags=[]
            if c["pk"]:tags.append("PK")
            if c["notnull"]:tags.append("NN")
            if c["name"] in unique.get(name,set()):tags.append("UQ/CI" if name=="operators" else "UQ")
            if c["default"] is not None:tags.append("="+str(c["default"]))
            label=f'{c["name"]} {c["type"]}'+(" "+",".join(tags) if tags else "")
            d.text(x+7,y+28+i*11.4,label,ha="left",size=9,
                   bounds=(x+3,y+20,w-6,h-20))
    d.relation([(265,246),(292,246)],source=nodes["reports"],target=nodes["report_events"])
    d.relation([(621,162),(621,194)],source=nodes["operators"],target=nodes["sessions"])
    d.relation([(265,330),(280,330),(280,378),(524,378)],start="many",finish="optionalone",
               source=nodes["reports"],target=nodes["teams"])
    d.text(389,365,"assigned_team_id → teams.id",size=9,label=True)
    d.shape(292,174,205,18,kind="blue",rounded=False)
    d.text(299,183,"UQ (client_id, sequence_number)",ha="left",size=9)
    d.text(292,207,"Không FK tới reports (payload/result_data).",ha="left",size=9)
    d.text(292,396,"PK: khóa chính; NN: NOT NULL; UQ: UNIQUE; CI: NOCASE.",ha="left",size=9)
    d.text(10,411,"Nét đứt: liên hệ do mã kiểm soát, DDL chưa khai báo FK. raw_payload lưu JSON; actor lưu tên thao tác.",ha="left",size=9)
    return d


def mobile():
    d=Diagram("mobile_architecture",418,"2.3 · Kiến trúc Flutter, phụ thuộc và tích hợp nền tảng",width=W)
    for y,h,title,kind in [(10,75,"PRESENTATION · GIAO DIỆN VÀ ĐIỀU PHỐI","blue"),
                           (108,105,"DOMAIN · HỢP ĐỒNG VÀ NGHIỆP VỤ DART","amber"),
                           (237,95,"DATA · HIỆN THỰC VÀ NGUỒN DỮ LIỆU","teal")]:
        section(d,10,y,708,h,title,glyph="layers",kind=kind)
    icon(d,"screen",27,44,21)
    lines(d,59,46,["HomeScreen · SOS; ComposeScreen · ảnh/khai báo", "HistoryScreen / SubmittedScreen · tiến trình", "Settings / AI models; main.dart khởi tạo phụ thuộc"],width=280,leading=12)
    icon(d,"clock",385,44,21)
    lines(d,415,46,["AppController · ChangeNotifier, WidgetsBindingObserver", "SOS, bài chi tiết, inference, retry, GPS, ImagePicker", "Trạng thái: 15 s khi theo dõi; mặc định 60 s"],width=289,leading=12)
    contracts=step(d,23,141,190,64,"Repository interfaces\nRescueRepository\nInferenceRepository\nNetworkRepository")
    usecases=step(d,244,141,265,64,"SendSosUseCase; SubmitRescuePostUseCase\nAnalyzeImageUseCase; GetRescueRecordsUseCase\nSyncPendingRecordsUseCase; deliverRecord\nAdaptiveSendPolicy; UrgencyLogisticModel")
    entities=step(d,541,141,164,64,"Entities / giá trị\nRescueRecord · AiTag\nSyncMessage · SendMode\nRescueStatus · SmsStatus\nid, GPS, urgency, payload")
    repos=step(d,23,267,207,54,"RescueRepositoryImpl\nInferenceRepositoryImpl\nNetworkRepositoryImpl")
    local=step(d,260,267,210,54,"RecordLocalDataSource; Hive\nOutboxLocalDataSource; Hive\nSyncMessageModel; core/sync: JCS + hash")
    remote=step(d,500,267,205,54,"SenderRemoteDataSource\nSyncRemoteDataSource\nNetworkRemoteDataSource\nInferenceLocalDataSource: native/web")
    d.arrow([(548,85),(548,97),(365,97),(365,141)],target=usecases,label="Gọi use case / policy",at=(452,97))
    d.arrow([(244,170),(213,170)],source=usecases,target=contracts)
    d.arrow([(509,170),(541,170)],source=usecases,target=entities)
    d.arrow([(23,286),(16,286),(16,171),(23,171)],dashed=True,source=repos,target=contracts)
    d.text(108,223,"Implements hợp đồng domain",size=9,label=True)
    d.arrow([(230,294),(260,294)],source=repos,target=local)
    d.arrow([(126,321),(126,343),(602,343),(602,321)],source=repos,target=remote)
    d.text(363,343,"Gọi datasource",size=9,label=True)
    for x,glyph,title,detail in [(15,"pin","GPS / ảnh","Geolocator · ImagePicker"),
                                 (195,"chip","AI native / web","ONNX · rescue/executorch"),
                                 (375,"sms","HTTP / SMS","FastAPI · rescue/sms"),
                                 (555,"clock","Đồng bộ nền","Workmanager ~15 phút")]:
        icon(d,glyph,x+4,365,22)
        d.text(x+36,367,title,ha="left",bold=True,size=9.5)
        d.text(x+4,390,detail,ha="left",size=9.1)
    d.text(10,410,"Liền: lời gọi; đứt: implements. Repository domain là hợp đồng; controller/datasource gọi plugin thiết bị.",ha="left",size=9)
    return d


def ingestion():
    d=Diagram("flow_05_backend_ingest_dedup",426,"2.12 · Ba đường tiếp nhận và cơ chế chống trùng",width=W)
    for x,w,title,glyph,kind in [(10,294,"A · JSON SYNC","document","blue"),
                                (326,192,"B · MULTIPART / ẢNH","camera","teal"),
                                (534,184,"C · SMS GATEWAY","sms","amber")]:
        section(d,x,10,w,385,title,glyph=glyph,kind=kind)
    a=step(d,20,50,274,48,"POST /sync/messages · Header v1\nJSON strict; ≤50 messages; ≤256 KiB\nSai request: HTTP 400; quá dung lượng: 413")
    b=step(d,20,122,274,58,"Từng message: cấu trúc + thời hạn TTL\nJCS (RFC 8785) → SHA-256; đối chiếu hash\nSai payload/hash hoặc hết hạn → rejected\nTra message_id, rồi cặp client_id/sequence_number")
    c=step(d,48,204,141,47,"Đã có ID\nhoặc client/seq?",diamond=True,kind="amber")
    dup=step(d,202,201,92,64,"Cùng ID + hash:\nduplicate\nKhác hash / seq:\nrejected",kind="amber")
    business=step(d,20,286,274,64,"Mới: CREATE_RESCUE_RECORD\nhoặc UPDATE_RESCUE_STATUS\nKiểm tra quyền gộp / quyền đổi trạng thái\nGhi nghiệp vụ + dedup; commit cùng transaction\naccepted; lỗi server → rollback / retry_later")
    result=step(d,20,369,274,23,"HTTP 200: results ACK theo message_id",kind="teal")
    d.arrow([(157,98),(157,122)],source=a,target=b)
    d.arrow([(119,180),(119,204)],source=b,target=c)
    d.arrow([(189,228),(202,228)],source=c,target=dup)
    d.arrow([(119,251),(119,286)],source=c,target=business,label="Chưa có",at=(148,270))
    d.arrow([(157,350),(157,369)],source=business,target=result)
    d.arrow([(294,151),(312,151),(312,380),(294,380)],dashed=True,source=b,target=result)
    d.arrow([(294,237),(312,237)],dashed=True,source=dup,heads=False)
    p1=step(d,336,50,172,48,"POST /api/reports\nHeader v1; meta ≤64 KiB\nJSON strict; meta.id + clientId")
    p2=step(d,336,123,172,48,"Kiểm tra report ID / chủ sở hữu\nowner_client_id: quyền bổ sung\n409: REPORT_ID_CONFLICT")
    p3=step(d,336,196,172,78,"Nếu có ảnh: ≤15 MiB mặc định\nSHA-256 + số byte phải khớp\nKiểm tra JPEG / PNG / WebP\nẢnh đầu được giữ; tệp uploads/\nLỗi: HTTP 400 / 413 / 415")
    p4=step(d,336,304,172,51,"Mới: status=processing\nĐã có: bổ sung trường còn trống\nDB lưu metadata + thông tin ảnh")
    p5=step(d,336,369,172,23,"HTTP 201 + id / imageUrl",kind="teal")
    for f,t,y1,y2 in [(p1,p2,98,123),(p2,p3,171,196),(p3,p4,274,304),(p4,p5,355,369)]:
        d.arrow([(422,y1),(422,y2)],source=f,target=t)
    s1=step(d,544,50,164,48,"POST /api/sms/inbound\nToken header hoặc query\nTắt: HTTP 403; sai token: 401")
    s2=step(d,544,123,164,48,"Parse SOS|id:...|pos:...\nGPS có thể unknown\nGiữ ID để HTTP gộp về sau")
    s3=step(d,544,196,164,65,"Tin tự do / thiếu ID:\nsms-{hash(sender,text,time)}\nKhông có tọa độ:\nđưa vào hàng xem xét")
    s4=step(d,544,295,164,60,"Nguồn SMS được trusted\nsave_report: tạo hoặc gộp\nGiữ dữ liệu và ảnh đã có\nLưu nguồn, số liên hệ")
    s5=step(d,544,369,164,23,"HTTP 201 mới / 200 gộp",kind="teal")
    for f,t,y1,y2 in [(s1,s2,98,123),(s2,s3,171,196),(s3,s4,261,295),(s4,s5,355,369)]:
        d.arrow([(626,y1),(626,y2)],source=f,target=t)
    d.text(10,403,"JSON sync: ID_REUSED_WITH_DIFFERENT_PAYLOAD / SEQUENCE_REUSED là lỗi ACK, không phải HTTP 409.",ha="left",size=9)
    d.text(10,418,"Nét đứt: gom ACK. Tệp ảnh nằm ngoài transaction SQLite; SMS không sử dụng bảng messages_dedup.",ha="left",size=9)
    return d


def lifecycle():
    d=Diagram("flow_08_dispatch_lifecycle",405,"2.19 · Vòng đời tác nghiệp, API và kiểm soát trạng thái",width=W)
    for x,w,title,glyph,kind in [(10,216,"1 · XÁC MINH CA","pin","blue"),
                                (254,216,"2 · ĐIỀU PHỐI","team","teal"),
                                (498,220,"3 · KẾT QUẢ / ĐÓNG","document","amber")]:
        section(d,x,10,w,334,title,glyph=glyph,kind=kind)
    schematic_map(d,23,48,76,48)
    lines(d,109,52,["Mở ca theo report ID", "Ảnh, AI, N, V, nguồn", "Đối chiếu hiện trường"],width=109,leading=13)
    loc=step(d,59,116,120,44,"Đủ vị trí?",diamond=True,kind="amber")
    locate=step(d,22,184,192,52,"Gọi xác minh; bổ sung tọa độ\nPUT /api/reports/{id}/location\nCó tọa độ: location_source=manual")
    note=step(d,22,275,192,60,"GPS phục vụ xác minh, không phải\nđiều kiện chặn /team hay /status.\nThiếu GPS vẫn có hàng xem xét.\nLỗi mạng không tự hủy ca.",kind="gray")
    teams=step(d,267,51,190,50,"Chọn đội còn hoạt động\nXem năng lực, địa bàn\nGET /api/teams")
    assign=step(d,267,126,190,52,"PUT /api/reports/{id}/team\nGhi assigned_team_id + event\nKhông tự đổi status")
    dispatch=step(d,267,203,190,50,"PATCH /api/reports/{id}/status\nstatus=dispatched\nstatusVersion > hiện tại")
    field=step(d,267,280,190,38,"Đội tiếp cận và cứu nạn\nTác nghiệp ngoài phần mềm",kind="gray")
    outcome=step(d,545,74,120,48,"Hoàn tất /\ncần đóng ca?",diamond=True,kind="amber")
    resolved=step(d,512,182,92,57,"resolved\nĐã hoàn tất\nPATCH /status",kind="teal")
    cancelled=step(d,616,182,92,57,"cancelled\nLý do bắt buộc\nPATCH /status",kind="red")
    audit=step(d,512,279,196,54,"reports + report_events\nactor, thời gian, from/to, version\nCa cuối được loại khỏi active",kind="white")
    d.arrow([(119,96),(119,116)],target=loc)
    d.arrow([(119,160),(119,184)],source=loc,target=locate,label="Thiếu",at=(139,173))
    d.arrow([(179,138),(239,138),(239,77),(267,77)],source=loc,target=teams,label="Có",at=(209,126))
    d.arrow([(214,210),(243,210),(243,88),(267,88)],source=locate,target=teams)
    for f,t,y1,y2 in [(teams,assign,101,126),(assign,dispatch,178,203),(dispatch,field,253,280)]:
        d.arrow([(362,y1),(362,y2)],source=f,target=t)
    d.arrow([(457,299),(482,299),(482,98),(545,98)],source=field,target=outcome)
    d.arrow([(545,98),(490,98),(490,329),(362,329),(362,318)],source=outcome,target=field,dashed=True)
    d.text(368,338,"Chưa xong: tiếp tục dispatched",size=9,label=True)
    d.arrow([(586,114),(586,158),(558,158),(558,182)],source=outcome,target=resolved)
    d.text(550,168,"Hoàn tất",size=9,label=True)
    d.arrow([(624,114),(624,158),(662,158),(662,182)],source=outcome,target=cancelled)
    d.text(668,168,"Đóng ca",size=9,label=True)
    d.arrow([(558,239),(558,279)],source=resolved,target=audit)
    d.arrow([(662,239),(662,279)],source=cancelled,target=audit)
    icon(d,"shield",15,361,21)
    lines(d,45,363,["API kiểm tra phiên điều phối, report ID, đội còn hoạt động và statusVersion tăng.",
                    "Không đi lùi thứ hạng; trạng thái cuối không chuyển sang trạng thái khác. Có thể đóng từ processing/dispatched.",
                    "Đường vẽ là quy trình tác nghiệp thông thường; lỗi kỹ thuật phải retry/xác minh, không tự coi là cancelled."],
          width=669,leading=14,size=9.2)
    return d


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir",type=Path,default=ROOT/"assets/diagrams")
    parser.add_argument("--review-dir",type=Path,default=REVIEW)
    args=parser.parse_args();args.review_dir.mkdir(parents=True,exist_ok=True)
    combined=ET.Element("mxfile",host="app.diagrams.net",version="26.0.0")
    result={};errors=[]
    for builder in [architecture,overview,mobile,erd,ingestion,lifecycle]:
        d=builder()
        try:
            result[d.name]=d.save(args.output_dir,args.review_dir/"previews")
        except ValueError as exc:
            errors.append(str(exc));continue
        combined.append(d.mx.find("diagram"))
        if hasattr(d,"schema_data"):
            (args.review_dir/"schema-from-ddl.json").write_text(json.dumps(d.schema_data,indent=2,ensure_ascii=False)+"\n")
        print(d.name,"PASS: bounds, vector PDF/SVG and editable Draw.io")
    if errors:raise SystemExit("\n".join(errors))
    ET.indent(combined)
    ET.ElementTree(combined).write(args.review_dir/"00-six-detailed-system-diagrams.drawio",encoding="utf-8",xml_declaration=True)
    sources=["products/be/main.py","products/be/storage.py","products/be/cluster_service.py","products/be/sms_intake.py",
             "products/fe/app/lib/main.dart","products/fe/app/lib/presentation/controllers/app_controller.dart",
             "products/fe/app/lib/domain/usecases/send_sos_usecase.dart","products/fe/app/lib/domain/usecases/deliver_record.dart",
             "products/fe/app/lib/data/models/rescue_record_payload.dart"]
    result={"figures":result,"sources_sha256":{p:hashlib.sha256((ROOT.parent/p).read_bytes()).hexdigest() for p in sources},
            "scripts_sha256":{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in [Path(__file__),ROOT/"scripts/build_system_diagrams.py"]}}
    (args.review_dir/"validation.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")


if __name__=="__main__":main()
