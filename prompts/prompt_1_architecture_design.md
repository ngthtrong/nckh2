# PROMPT 1 — Mobile Application Architecture Design

> **Target**: AI Agent responsible for system architecture design
> **Project**: "An Edge AI–Based System for Multimodal Analysis and Clustering of Flood Rescue Events"
> **Deliverable for**: Progress Report #1 to the supervising professor
> **Language for deliverables**: Vietnamese (technical terms in English where appropriate)

---

## YOUR ROLE

You are a senior software architect specializing in mobile AI applications. Your task is to produce a **complete architecture design document** for a mobile-first flood rescue system that runs AI inference on-device (Edge AI). The document will be presented to the supervising professor as part of the first progress report.

---

## PROJECT CONTEXT

### Problem Statement
During flood/typhoon disasters in Central Vietnam, telecom infrastructure is often disrupted or overloaded. Current rescue coordination systems depend on stable internet, making them ineffective at the critical moment. This project builds a **mobile application** that:
1. Runs lightweight AI models **on-device** (Edge AI) to classify flood images and Vietnamese rescue text messages by urgency level.
2. Transmits only compact metadata (a few KB) instead of raw images/videos when connectivity is poor.
3. Clusters duplicate rescue events by geo-location and semantics on the server side.
4. Displays a real-time rescue priority map on a web dashboard.

### Technology Stack (as specified in the research proposal)
- **Mobile App**: Flutter (Dart) — cross-platform, single codebase
- **On-device AI Runtime**: TensorFlow Lite / ONNX Runtime Mobile
- **Backend Server**: Python (FastAPI or Flask)
- **Database**: PostgreSQL + PostGIS (spatial data)
- **AI Models**:
  - Image classification: MobileNetV3 / EfficientNet-Lite (TFLite)
  - Text classification: PhoBERT (distilled) / DistilBERT (ONNX)
- **Dashboard**: Web-based map visualization (Leaflet.js or Mapbox)
- **Communication protocol**: REST API + WebSocket for real-time updates
- **Key constraint**: The system must function in degraded network conditions (2G/3G or intermittent connectivity)

### Team Members (5 people)
| Name | Responsibilities |
|---|---|
| Lê Thị Ngọc Ảnh | Data collection & labeling, AI model training, Backend & Dashboard |
| Nguyễn Như Quỳnh | AI model training, Backend & Dashboard, System testing |
| Nguyễn Thanh Trọng | System architecture, Geo-clustering algorithm, Mobile app |
| Ngô Hưng Thịnh | Data collection, Model compression, Geo-clustering algorithm |
| Cao Tường Hưng | System architecture, Model compression, Mobile app |

---

## DELIVERABLES REQUIRED

You must produce **ALL** of the following. Each deliverable must be complete, production-quality, and ready to present.

### Deliverable 1: System Architecture Overview Diagram

Create a **high-level system architecture diagram** showing:
- **Mobile App** (Flutter) — with AI inference engine on-device
- **Backend Server** (Python) — with clustering engine
- **Database** (PostgreSQL + PostGIS)
- **Web Dashboard** — real-time map
- **Data flow** between all components (include both online and offline/degraded-network paths)
- The programming languages/frameworks used at each layer

**IMPORTANT: Clearly show the TWO data flow paths:**
1. **Normal connectivity**: Full data sync (images, text, GPS, AI results → Server)
2. **Degraded connectivity (2G/offline)**: Only compact metadata JSON (AI classification result + GPS + urgency score + text summary) is transmitted

**Format requirements:**
- Produce the diagram in **BOTH** Mermaid syntax AND PlantUML (.puml) syntax
- Use Vietnamese labels for component names
- Include a legend explaining colors/line styles

### Deliverable 2: Mobile App Internal Architecture Diagram

Create a **detailed internal architecture diagram** of the Flutter mobile application, showing:

- **Presentation Layer**: UI screens (Home, Camera/Gallery, Text Input, Rescue Request Form, History, Settings)
- **Business Logic Layer**: State management (BLoC/Provider/Riverpod — pick one and justify), use cases
- **AI Inference Layer**: 
  - Image classification pipeline (camera → preprocessing → TFLite model → result)
  - Text classification pipeline (input → tokenization → ONNX model → result)
  - Urgency score calculation (combining image + text results)
- **Data Layer**: 
  - Local storage (SQLite/Hive for offline queue)
  - Network service (REST API client, WebSocket client)
  - Sync manager (queue → retry → send when connected)
- **Platform Layer**: Camera, GPS, Network status detection, Battery optimization

**Format requirements:**
- Produce in **BOTH** Mermaid AND PlantUML syntax
- Show dependencies between layers (top-down)
- Use Vietnamese labels

### Deliverable 3: Module Description Table

Create a detailed table listing all **main modules** of the system:

| # | Tên Module | Mô tả chức năng | Công nghệ sử dụng | Người phụ trách |
|---|---|---|---|---|
| 1 | ... | ... | ... | ... |

Include at minimum these modules:
1. Camera & Image Capture Module
2. Image Classification AI Module (on-device)
3. Text Input & Processing Module
4. Text Classification AI Module (on-device)
5. Urgency Score Calculator
6. Offline Data Queue & Sync Manager
7. GPS & Location Service
8. Network Status Monitor
9. REST API Client
10. Backend API Server
11. Spatial Clustering Engine (DBSCAN/HDBSCAN on server)
12. Database (PostgreSQL + PostGIS)
13. Web Dashboard & Map Visualization
14. User Authentication (if applicable)

### Deliverable 4: Technology Stack Summary Diagram

Create a visual summary showing ALL technologies/languages used, organized by layer:

```
Tầng trình bày (Frontend):  Flutter (Dart), HTML/CSS/JS (Dashboard)
Tầng xử lý AI tại biên:    TensorFlow Lite, ONNX Runtime Mobile
Tầng nghiệp vụ (Backend):  Python, FastAPI
Tầng dữ liệu:              PostgreSQL, PostGIS, SQLite (mobile local)
Tầng giao tiếp:             REST API, WebSocket
```

**Format**: Produce as both a Mermaid diagram and a PlantUML diagram. Make it visually clean and presentation-ready.

### Deliverable 5: Data Flow Sequence Diagram

Create a **sequence diagram** (UML) showing the complete flow of a rescue request:

1. User opens app → takes photo OR enters text
2. On-device AI classifies the image (flood level: none/low/high)
3. On-device AI classifies the text (urgency: urgent_rescue/need_supplies/safe_update/irrelevant)
4. System calculates composite urgency score
5. System checks network connectivity
6. **If connected**: Send full data to server
7. **If disconnected/weak**: Queue compact metadata locally, retry when connected
8. Server receives data → runs spatial clustering → updates dashboard map
9. Dashboard shows clustered rescue events with priority colors

**Format**: Both Mermaid `sequenceDiagram` and PlantUML sequence diagram.

---

## OUTPUT FORMAT

Produce a single Markdown document structured as follows:

```markdown
# THIẾT KẾ KIẾN TRÚC HỆ THỐNG
## Hệ thống phân tích đa phương thức và phân cụm sự kiện cứu hộ bão lũ dựa trên Edge AI

### 1. Sơ đồ kiến trúc tổng quan hệ thống
#### 1.1. Mermaid
[mermaid code]
#### 1.2. PlantUML
[puml code]
#### 1.3. Mô tả
[Vietnamese description of the architecture]

### 2. Sơ đồ kiến trúc chi tiết ứng dụng di động
#### 2.1. Mermaid
[mermaid code]
#### 2.2. PlantUML
[puml code]
#### 2.3. Mô tả
[Vietnamese description]

### 3. Bảng mô tả các module chính
[Table in Vietnamese]

### 4. Sơ đồ tổng hợp công nghệ sử dụng
#### 4.1. Mermaid
[mermaid code]
#### 4.2. PlantUML
[puml code]

### 5. Sơ đồ tuần tự luồng xử lý yêu cầu cứu hộ
#### 5.1. Mermaid
[mermaid code]
#### 5.2. PlantUML
[puml code]
#### 5.3. Mô tả
[Vietnamese description of the flow]
```

---

## QUALITY REQUIREMENTS

1. **Completeness**: Every component mentioned in the research proposal must appear in the diagrams.
2. **Consistency**: Technology names must match exactly between diagrams and tables.
3. **Edge AI emphasis**: The on-device AI processing must be clearly highlighted as the core differentiator. Show that inference happens ON the phone, NOT on the server.
4. **Offline-first design**: The architecture must clearly show how the system handles network outages gracefully.
5. **Vietnamese context**: Use Vietnamese labels. Reference Central Vietnam flood scenarios.
6. **Presentation-ready**: The diagrams should be clean enough to put directly into a progress report slide deck.
7. **Valid syntax**: All Mermaid and PlantUML code must be syntactically correct and renderable.

---

## CONSTRAINTS

- Do NOT include any code implementation — this is architecture design only.
- Do NOT design the database schema (that will be done separately).
- Do NOT discuss AI model selection or training — that is handled by another workstream.
- Focus ONLY on architecture, modules, technology stack, and data flow.
