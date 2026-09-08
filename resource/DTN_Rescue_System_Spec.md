# DTN Rescue Offline Communication — System Specification, Test Plan & Agent Rules

## 1. Mục tiêu

Xây dựng và đánh giá cơ chế truyền thông tin cứu hộ trong khu vực bị cô lập hoặc mạng gián đoạn bằng:

- Điện thoại Android thật làm rescue nodes.
- Store–Carry–Forward / Delay-Tolerant Networking (DTN).
- Bundle/Message chỉ chứa thông tin tối thiểu sau Edge AI:
  - `time`
  - `location`
  - `message`
  - `priority`
  - `image_label`
- Mobile Data Mule mô phỏng UAV trong simulator.
- Gateway/Data Mule đưa bundle ra khỏi vùng cô lập rồi upload lên server.

Mục tiêu nghiên cứu không phải chứng minh UAV thật bay được, mà đánh giá:
1. khả năng giữ và chuyển tiếp thông tin khi offline;
2. ảnh hưởng của buffer, bandwidth và contact window;
3. khả năng ưu tiên thông tin CRITICAL;
4. hiệu quả của Mobile Data Mule trong việc đưa dữ liệu ra khỏi isolated cluster.

---

## 2. Kiến trúc hệ thống

```text
                         INTERNET
                            |
                         Gateway
                            |
                     +------+------+
                     |             |
                  4G/5G        Server
                     |
                 Data Mule
              (UAV simulated)
                     |
              +------+------+
              |             |
          Contact       Contact
              |             |
          +---+-------------+---+
          | Isolated Cluster     |
          |                      |
          | Phone A <-> Phone B  |
          |    ^          ^      |
          |    |          |      |
          | Phone C <-> Phone D  |
          +----------------------+
```

### Các thành phần

**Rescue Node**
- Android phone thật.
- Tạo rescue report.
- Chạy Edge AI hoặc nhận kết quả Edge AI.
- Lưu bundle vào local SQLite/Room.
- Discovery và transfer qua BLE/Wi-Fi Direct.

**Bundle Store**
- Persistent local queue.
- Không xóa bundle ngay khi gửi.
- Có trạng thái: `PENDING`, `FORWARDED`, `DELIVERED`, `EXPIRED`, `DROPPED`.

**Routing/Forwarding Engine**
- Quyết định bundle nào được gửi khi xuất hiện contact.
- Baseline: FIFO.
- Baseline DTN: Epidemic hoặc Spray-and-Wait.
- Baseline thông minh: Priority + TTL.
- Proposed: Priority + TTL + contact-aware forwarding.

**Mobile Data Mule**
- UAV chỉ là node di động trong simulation.
- Có buffer hữu hạn.
- Có trajectory, tốc độ, communication range và contact window.
- Khi ra khỏi disaster area và gặp gateway thì forward bundle lên server.

**Gateway/Server**
- Nhận bundle.
- Kiểm tra integrity.
- Loại duplicate.
- Reconstruct event/report.
- Ghi thời điểm delivery.

---

## 3. Bundle format

Prototype có thể dùng JSON; experiment nên có thêm một profile compact/binary.

Ví dụ:

```json
{
  "id": "bundle-000001",
  "time": 1756056031,
  "location": [10.0342, 105.7228],
  "message": "3 người mắc kẹt tầng 2",
  "priority": 4,
  "image_label": "person_trapped",
  "confidence": 0.96,
  "ttl": 3600
}
```

Khuyến nghị ngân sách thiết kế:

- Typical payload: 300–800 bytes.
- Conservative test size: **1 KB/bundle**.
- Không đưa ảnh gốc vào baseline chính.
- Nếu cần ảnh, tách thành một loại payload khác và đánh giá riêng.

### Ước lượng sức chứa

Với 1 KB/bundle:

| Buffer | Bundle tối đa lý thuyết |
|---:|---:|
| 100 KB | ~100 |
| 512 KB | ~512 |
| 1 MB | ~1,000 |
| 5 MB | ~5,000 |
| 10 MB | ~10,000 |
| 50 MB | ~50,000 |

Đây là sức chứa lưu trữ, không phải số bundle chắc chắn truyền được trong một contact.

---

## 4. Công thức quan trọng

### 4.1. Contact capacity

Xấp xỉ:

`capacity_bytes = bandwidth_bytes_per_sec × contact_time_sec × efficiency`

Ví dụ:
- bandwidth = 100 KB/s
- contact = 60 s
- efficiency = 0.7

=> khoảng 4.2 MB hữu dụng.

Với bundle 1 KB:

=> khoảng 4,200 bundle/contact.

### 4.2. Delivery Ratio

`Delivery Ratio = delivered bundles / created bundles`

Nên báo cáo riêng:
- Overall Delivery Ratio
- Critical Delivery Ratio

### 4.3. Average Delivery Delay

`delay = delivery_time - creation_time`

Nên tính:
- mean
- median
- P95

### 4.4. Buffer Drop Ratio

`Buffer Drop Ratio = dropped_due_to_buffer / created`

### 4.5. Contact Completion Ratio

`Contact Completion = bundles_fully_transferred / bundles_selected_for_transfer`

Chỉ số này đặc biệt quan trọng vì contact window ngắn có thể khiến bundle không truyền xong.

---

# 5. Bộ test case đề xuất

## A. Baseline — Không có Data Mule

**Mục đích:** chứng minh isolated cluster không thể tự đưa dữ liệu ra ngoài nếu không có exit opportunity.

- 20 phones.
- Cluster: 1 km × 1 km.
- Internet: OFF.
- Simulation: 60 phút.
- Bundle: 1 KB.
- Không có gateway reachable.

Kỳ vọng:
- Internal delivery có thể xảy ra.
- External delivery = 0%.

---

## B. Data Mule cơ bản

- 20 rescue nodes.
- 1 Data Mule.
- Cluster: 1 km × 1 km.
- Data Mule range: 100 m.
- Speed: 10 m/s.
- Buffer: 10 MB.
- Bundle: 1 KB.
- Contact bandwidth: 100 KB/s.
- Contact window mục tiêu: 30–60 s.
- Data Mule ra gateway sau khi thu dữ liệu.

Biến quan sát:
- delivery ratio;
- average delay;
- critical delivery ratio.

---

## C. Ảnh hưởng của Buffer

Giữ các tham số khác cố định.

| Case | Buffer |
|---|---:|
| B1 | 1 MB |
| B2 | 5 MB |
| B3 | 10 MB |
| B4 | 50 MB |

Bundle: 1 KB.

Mục tiêu:
- tìm điểm buffer saturation;
- đo buffer drop ratio;
- kiểm tra buffer lớn có thực sự cải thiện delivery hay không.

---

## D. Ảnh hưởng Contact Window

| Case | Contact time |
|---|---:|
| C1 | 5 s |
| C2 | 10 s |
| C3 | 30 s |
| C4 | 60 s |
| C5 | 120 s |

Bandwidth: 100 KB/s.

Với efficiency 70%, capacity hữu dụng xấp xỉ:

| Contact | Capacity |
|---:|---:|
| 5 s | 350 KB |
| 10 s | 700 KB |
| 30 s | 2.1 MB |
| 60 s | 4.2 MB |
| 120 s | 8.4 MB |

Với bundle 1 KB, đây tương đương khoảng:
350 / 700 / 2,100 / 4,200 / 8,400 bundle/contact.

---

## E. Ảnh hưởng Bandwidth

| Case | Bandwidth |
|---|---:|
| D1 | 25 KB/s |
| D2 | 50 KB/s |
| D3 | 100 KB/s |
| D4 | 250 KB/s |
| D5 | 500 KB/s |

Contact = 30 s.

Dùng để kiểm tra contact-window bottleneck.

---

## F. Ảnh hưởng tần suất UAV

| Case | UAV visit interval |
|---|---:|
| F1 | 2 min |
| F2 | 5 min |
| F3 | 10 min |
| F4 | 20 min |
| F5 | 30 min |

Mục tiêu:
- đo delay;
- tìm trade-off giữa số lần visit và delivery;
- xác định Critical Delivery Delay.

---

## G. Routing comparison

Chạy cùng mobility/contact trace:

1. FIFO
2. Epidemic
3. Spray-and-Wait
4. Priority + TTL
5. Proposed Contact-Aware Priority

Metrics:
- Overall Delivery Ratio
- Critical Delivery Ratio
- Average Delay
- P95 Delay
- Overhead
- Buffer Drop Ratio
- Bytes transmitted

---

## H. Priority stress test

Tạo 10,000 bundles:

- 10% CRITICAL
- 20% HIGH
- 40% NORMAL
- 30% LOW

Giới hạn contact capacity.

So sánh FIFO với Priority-aware.

Mục tiêu chính:

`Critical Delivery Ratio`

và

`Critical P95 Delivery Delay`.

Giả thuyết:
- FIFO có thể lãng phí contact capacity vào message ít quan trọng.
- Priority-aware phải ưu tiên CRITICAL.
- Proposed method phải giữ lợi thế khi contact window ngắn.

---

## I. TTL test

TTL:

- 1 min
- 5 min
- 15 min
- 30 min
- 60 min

Đo:
- delivery;
- expired ratio;
- delay.

TTL ngắn phải làm tăng expired bundles nhưng có thể giảm buffer pressure.

---

## J. Message generation stress test

Bundle generation:

| Case | Rate |
|---|---:|
| J1 | 1/s |
| J2 | 5/s |
| J3 | 10/s |
| J4 | 50/s |
| J5 | 100/s |

Bundle size = 1 KB.

Buffer = 10 MB.

Mục tiêu:
- xác định saturation point;
- đo queue growth;
- đo critical message survival.

---

# 6. Test matrix tối thiểu nên chạy

Không cần chạy toàn bộ Cartesian product ngay từ đầu.

### Phase 1 — Feasibility
- 20 nodes
- 1 Data Mule
- 10 MB buffer
- 1 KB bundle
- 100 KB/s
- 60 s contact
- 10 min visit

### Phase 2 — Sensitivity
Thay từng biến:
- buffer;
- bandwidth;
- contact window;
- visit interval.

### Phase 3 — Routing
- FIFO
- Epidemic
- Spray-and-Wait
- Priority + TTL
- Proposed

### Phase 4 — Stress
- 100 / 500 / 1,000 / 5,000 / 10,000 bundles
- 10/20/50/100 nodes.

### Phase 5 — Real-device validation
3–5 Android phones:
- offline creation;
- local persistence;
- BLE/Wi-Fi transfer;
- duplicate prevention;
- checksum/integrity;
- reconnect and resume.

---

# 7. Real-device test

Không cần UAV thật.

Một Android phone có thể đóng vai Data Mule.

```text
Phone A ──BLE──> Phone B
                  |
                  | movement
                  v
             "Data Mule"
                  |
                 4G
                  |
                  v
                Server
```

Kiểm tra:

1. Tạo report khi Internet OFF.
2. Kill app/reboot phone.
3. Xác nhận bundle vẫn còn.
4. Đưa phone B vào phạm vi A.
5. Forward bundle.
6. B ra khỏi cluster.
7. B có Internet.
8. Upload server.
9. Server ACK.
10. Xác nhận duplicate không xuất hiện.

---

# 8. Simulation tool

## ONE Simulator

ONE (Opportunistic Networking Environment) được thiết kế riêng cho đánh giá DTN/opportunistic networking, hỗ trợ mobility models, routing protocols, message exchange, visualization và reports. Nó đã được sử dụng rộng rãi trong nghiên cứu DTN. 

Reference:
- Keränen, Ott, Kärkkäinen, *The ONE Simulator for DTN Protocol Evaluation*, SimuTools 2009.
- Keränen, Kärkkäinen, Ott, *Simulating Mobility and DTNs with the ONE*, Journal of Communications, 2010.

## Khi dùng ONE

Mô hình hóa:

```text
Phone = pedestrian/static node
UAV = mobile Data Mule
Gateway = stationary Internet node
Disaster Area = geographic region
```

UAV có thể dùng predefined trajectory.

---

# 9. Paper / tài liệu đáng chú ý

## [P1] RFC 9171 — Bundle Protocol Version 7

Nguồn chuẩn về BPv7.

Cần đọc:
- bundle;
- bundle node;
- store-carry-forward;
- convergence layer;
- fragmentation;
- lifetime/expiration;
- hop count;
- delivery/forwarding reports.

RFC 9171 xác định BPv7 là Internet Standards Track và mô tả DTN/BP như một store-carry-forward overlay; routing algorithm và convergence-layer implementation không được BPv7 quy định cụ thể. 

Official:
https://www.rfc-editor.org/rfc/rfc9171

---

## [P2] Keränen et al. — The ONE Simulator for DTN Protocol Evaluation

Dùng để biện minh việc sử dụng ONE trong simulation.

Điểm quan trọng:
- DTN;
- mobility;
- routing;
- application;
- synthetic mobility;
- real-world traces.

---

## [P3] Designing delay constrained hybrid ad hoc network infrastructure for post-disaster communication

Rất sát domain cứu hộ.

Keywords:
- Delay Tolerant Network;
- disaster management;
- Data Mule;
- hybrid network.

Paper nghiên cứu việc dùng DTN/mobile phone và Data Mule trong post-disaster communication, đồng thời chỉ ra latency và delivery probability là vấn đề quan trọng trong mạng diện rộng. 

---

## [P4] Routing Protocols for Delay Tolerant Networks: A Reference Architecture and a Thorough Quantitative Evaluation

Có giá trị cho phần benchmark routing.

Sử dụng ONE để đánh giá nhiều DTN routing protocols và mobility models. 

---

## [P5] Energy-Aware Forwarding Strategies for DTN Routing Protocols

Có giá trị nếu nghiên cứu thêm:
- energy;
- forwarding;
- mobility;
- buffer;
- ONE.

ONE được dùng để mô phỏng movement, contacts, forwarding và message handling. 

---

## [P6] Recent field validation: LoRa + Store-Carry-Forward

Một nghiên cứu thực địa gần đây sử dụng mobile nodes/data mules trong bối cảnh flood/disaster và chỉ ra **contact-window bottleneck**: tăng range không đủ nếu throughput không đủ để truyền toàn bộ bundle trong thời gian tiếp xúc. 

Dùng paper này để củng cố việc đưa `contact window` vào test matrix.

---

# 10. Research hypothesis

### H1
Data Mule làm tăng External Delivery Ratio so với isolated cluster không có Data Mule.

### H2
Giảm contact window làm giảm Delivery Ratio và tăng Delivery Delay.

### H3
Tăng bandwidth cải thiện số bundle truyền thành công trong mỗi contact.

### H4
Priority-aware forwarding làm tăng Critical Delivery Ratio so với FIFO.

### H5
Priority + TTL + Contact Awareness đạt Critical Delivery Delay thấp hơn các baseline trong điều kiện contact window hạn chế.

### H6
Edge AI metadata-only representation làm giảm communication load đáng kể so với truyền ảnh gốc.

---

# 11. Agent Rules

Agent phải tuân thủ các rule sau khi phát triển hệ thống:

## Architecture

1. MUST treat rescue information as persistent data.
2. MUST NOT assume continuous Internet connectivity.
3. MUST store a locally created bundle before attempting transmission.
4. MUST support retry after failed contact.
5. MUST use unique `bundle_id`.
6. MUST use `created_at` and `ttl`.
7. MUST prevent duplicate delivery using `bundle_id`.
8. MUST maintain bundle state explicitly.
9. MUST separate application data, bundle management, routing, and transport.
10. MUST treat UAV as a Mobile Data Mule abstraction, not as a hard dependency.

## Bundle

11. Default research payload MUST contain:
    - time
    - location
    - message
    - priority
    - image_label

12. Default simulation bundle size SHOULD be 1 KB.
13. The system SHOULD support a configurable bundle size.
14. Original image MUST NOT be part of the metadata-only baseline.
15. If image transfer is added, it MUST be evaluated as a separate experiment.

## Forwarding

16. Agent MUST NOT forward all bundles blindly in the proposed method.
17. Agent MUST consider priority.
18. Agent MUST consider TTL.
19. Agent SHOULD consider contact duration.
20. Agent SHOULD estimate whether a selected bundle can finish transmission during the current contact.
21. CRITICAL bundles MUST receive higher forwarding priority.
22. Expired bundles MUST be removed.
23. Buffer overflow MUST produce an explicit drop event.

## Simulation

24. UAV MUST be represented as a mobile node.
25. UAV trajectory MUST be configurable.
26. Communication range MUST be configurable.
27. Contact duration MUST be measurable.
28. Bandwidth MUST be configurable.
29. Buffer size MUST be configurable.
30. Visit interval MUST be configurable.
31. Random seeds MUST be recorded for reproducibility.
32. Every experiment MUST record configuration parameters.

## Evaluation

33. MUST report Overall Delivery Ratio.
34. MUST report Critical Delivery Ratio.
35. MUST report Average Delivery Delay.
36. SHOULD report P95 Delivery Delay.
37. MUST report Buffer Drop Ratio.
38. SHOULD report communication overhead.
39. SHOULD report contact completion ratio.
40. Results MUST compare against at least FIFO and one established DTN routing baseline.

## Real-device validation

41. MUST test offline report creation.
42. MUST test persistence after connectivity loss.
43. MUST test duplicate prevention.
44. MUST test transfer after a later contact.
45. MUST record actual transfer time and payload size.
46. MUST NOT claim UAV hardware validation if only UAV simulation is performed.

## Scientific integrity

47. Simulation numbers MUST NOT be presented as real-world measurements.
48. Example values MUST be clearly labeled as assumptions/examples.
49. Real-device results MUST be separated from simulation results.
50. Any claimed improvement MUST be supported by repeated experiments and statistical summary.

---

# 12. Recommended first experiment

Use this as the initial reproducible configuration:

```text
Area                 = 1 km × 1 km
Rescue nodes         = 20
Data Mules           = 1
Gateway              = 1
Bundle size          = 1 KB
Buffer               = 10 MB
Bandwidth            = 100 KB/s
Communication range  = 100 m
Contact window       = 60 s
UAV speed            = 10 m/s
UAV visit interval   = 10 min
Simulation duration  = 60 min

Traffic:
CRITICAL = 10%
HIGH     = 20%
NORMAL   = 40%
LOW      = 30%

Routing:
FIFO
Epidemic/Spray-and-Wait
Priority + TTL
Proposed Contact-Aware Priority
```

Run each configuration with at least 10 different random seeds before drawing conclusions.

---

# 13. Core research story

The system should be framed as:

**Edge AI → Information Compression/Prioritization → DTN Bundle Store → Opportunistic Contact → Mobile Data Mule → Gateway → Rescue Server**

The key research problem is:

> When a disaster isolates a cluster and communication opportunities are short and intermittent, how can the system maximize delivery of high-priority rescue information under limited bandwidth, buffer, and contact time?

The UAV is only one possible Data Mule implementation. The abstraction should remain general enough to represent:
- UAV;
- rescue vehicle;
- boat;
- mobile gateway;
- person carrying a phone.

This keeps the research contribution broader than a specific drone platform.
