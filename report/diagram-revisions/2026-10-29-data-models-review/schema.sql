-- THIẾT KẾ ĐỀ XUẤT ĐỂ REVIEW. Không phải migration của backend hiện tại.
-- Chỉ chạy trong SQLite :memory: để dựng PDM và kiểm tra ràng buộc.
PRAGMA foreign_keys = ON;

CREATE TABLE sources (
    id TEXT NOT NULL PRIMARY KEY,
    kind TEXT NOT NULL CHECK (kind IN ('app','sms','hotline','synthetic')),
    source_family TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    phone TEXT,
    members INTEGER CHECK (members >= 0),
    note TEXT,
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1)),
    created_at TEXT NOT NULL
);

CREATE TABLE operators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    display_name TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'operator' CHECK (role IN ('admin','operator')),
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1)),
    must_change_password INTEGER NOT NULL DEFAULT 0 CHECK (must_change_password IN (0,1)),
    created_at TEXT NOT NULL,
    last_login_at TEXT
);

-- Giữ toàn bộ cột của bảng reports hiện tại; thêm các cột thuật toán tường minh.
-- Intake vẫn nhận dữ liệu thiếu; snapshot đủ dữ liệu ở analysis_members dùng NOT NULL.
CREATE TABLE reports (
    id TEXT NOT NULL PRIMARY KEY,
    server_received_at TEXT NOT NULL,
    created_at TEXT,
    lat REAL CHECK (lat BETWEEN -90 AND 90),
    lng REAL CHECK (lng BETWEEN -180 AND 180),
    trapped_count INTEGER DEFAULT 0 CHECK (trapped_count >= 0),
    injured_count INTEGER DEFAULT 0 CHECK (injured_count >= 0),
    vulnerable_groups TEXT,
    description TEXT,
    ai_tags TEXT,
    send_mode TEXT,
    status TEXT NOT NULL DEFAULT 'processing'
        CHECK (status IN ('processing','dispatched','resolved','cancelled')),
    status_version INTEGER NOT NULL DEFAULT 1 CHECK (status_version > 0),
    image_filename TEXT,
    image_local_path TEXT,
    image_url TEXT,
    image_sha256 TEXT,
    image_size_bytes INTEGER CHECK (image_size_bytes >= 0),
    raw_payload TEXT NOT NULL,
    first_received_at TEXT,
    updated_seq INTEGER DEFAULT 0,
    assigned_team_id INTEGER REFERENCES teams(id),
    location_source TEXT,
    close_reason TEXT,
    status_updated_at TEXT,
    owner_client_id TEXT,
    source_id TEXT REFERENCES sources(id),
    flood REAL CHECK (flood BETWEEN 0 AND 1),
    urgency_lr REAL CHECK (urgency_lr BETWEEN 0 AND 1),
    urgency REAL CHECK (urgency BETWEEN 0 AND 1),
    people_count REAL CHECK (people_count >= 0),
    vulnerability REAL CHECK (vulnerability >= 0),
    urgency_flags_json TEXT,
    ai_model_version TEXT,
    lr_model_version TEXT,
    provenance_quality REAL CHECK (provenance_quality BETWEEN 0 AND 1),
    CHECK ((lat IS NULL) = (lng IS NULL)),
    CHECK (status != 'cancelled' OR close_reason IS NOT NULL)
);

CREATE TABLE report_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id TEXT NOT NULL REFERENCES reports(id),
    kind TEXT NOT NULL,
    from_value TEXT,
    to_value TEXT,
    status_version INTEGER,
    actor TEXT,
    source TEXT NOT NULL,
    note TEXT,
    created_at TEXT NOT NULL,
    operator_id INTEGER REFERENCES operators(id)
);

CREATE TABLE sessions (
    token_hash TEXT NOT NULL PRIMARY KEY,
    operator TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    operator_id INTEGER NOT NULL REFERENCES operators(id)
);

CREATE TABLE messages_dedup (
    message_id TEXT NOT NULL PRIMARY KEY,
    client_id TEXT NOT NULL,
    sequence_number INTEGER NOT NULL CHECK (sequence_number >= 0),
    operation_type TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    error_code TEXT,
    result_data TEXT,
    created_at TEXT NOT NULL,
    expires_at TEXT,
    processed_at TEXT NOT NULL,
    report_id TEXT REFERENCES reports(id),
    UNIQUE (client_id, sequence_number)
);

CREATE TABLE server_meta (
    key TEXT NOT NULL PRIMARY KEY,
    value TEXT NOT NULL
);

-- Mỗi cấu hình là một phiên bản bất biến, được analysis_runs tham chiếu.
CREATE TABLE algorithm_configs (
    id TEXT NOT NULL PRIMARY KEY,
    label TEXT NOT NULL,
    created_at TEXT NOT NULL,
    formula_version TEXT NOT NULL,
    graph_mode TEXT NOT NULL CHECK (graph_mode IN ('product','additive')),
    community_algorithm TEXT NOT NULL CHECK (community_algorithm IN ('louvain','leiden')),
    sigma_geo_m REAL NOT NULL CHECK (sigma_geo_m > 0),
    tau_t_min REAL NOT NULL CHECK (tau_t_min > 0),
    tau_f REAL NOT NULL CHECK (tau_f > 0),
    tau_e REAL NOT NULL CHECK (tau_e > 0),
    alpha REAL NOT NULL CHECK (alpha >= 0),
    beta REAL NOT NULL CHECK (beta >= 0),
    gamma REAL NOT NULL CHECK (gamma >= 0),
    quantile_q REAL NOT NULL CHECK (quantile_q > 0 AND quantile_q < 1),
    top_k INTEGER NOT NULL CHECK (top_k > 0),
    resolution REAL NOT NULL CHECK (resolution > 0),
    random_seed INTEGER NOT NULL,
    q_b0 REAL NOT NULL,
    q_b1 REAL NOT NULL,
    q_b2 REAL NOT NULL,
    corrob_radius_m REAL NOT NULL CHECK (corrob_radius_m > 0),
    corrob_window_min REAL NOT NULL CHECK (corrob_window_min > 0),
    omega_e REAL NOT NULL CHECK (omega_e >= 0),
    omega_f REAL NOT NULL CHECK (omega_f >= 0),
    omega_n REAL NOT NULL CHECK (omega_n >= 0),
    mu REAL NOT NULL CHECK (mu BETWEEN 1 AND 2),
    v_scale REAL NOT NULL CHECK (v_scale > 0),
    n_ref REAL NOT NULL CHECK (n_ref > 0),
    n_claim_cap REAL NOT NULL CHECK (n_claim_cap > 0),
    v_cap REAL NOT NULL CHECK (v_cap > 0),
    near_distance_m REAL NOT NULL CHECK (near_distance_m >= 0),
    near_time_min REAL NOT NULL CHECK (near_time_min >= 0),
    near_f_abs REAL NOT NULL CHECK (near_f_abs >= 0),
    near_e_abs REAL NOT NULL CHECK (near_e_abs >= 0),
    near_n_floor REAL NOT NULL CHECK (near_n_floor >= 0),
    near_n_relative REAL NOT NULL CHECK (near_n_relative >= 0),
    near_v_abs REAL NOT NULL CHECK (near_v_abs >= 0),
    near_q_abs REAL NOT NULL CHECK (near_q_abs >= 0),
    require_same_source_family INTEGER NOT NULL CHECK (require_same_source_family IN (0,1)),
    require_same_image_state INTEGER NOT NULL CHECK (require_same_image_state IN (0,1)),
    lr_intercept REAL NOT NULL,
    lr_coef_1 REAL NOT NULL,
    lr_coef_2 REAL NOT NULL,
    lr_coef_3 REAL NOT NULL,
    lr_coef_4 REAL NOT NULL,
    lr_coef_5 REAL NOT NULL,
    lr_threshold REAL NOT NULL CHECK (lr_threshold BETWEEN 0 AND 1),
    lr_feature_order_json TEXT NOT NULL,
    flood_mapping_json TEXT NOT NULL,
    CHECK (abs(omega_e + omega_f + omega_n - 1) < 0.000000001)
);

CREATE TABLE analysis_runs (
    id TEXT NOT NULL PRIMARY KEY,
    config_id TEXT NOT NULL REFERENCES algorithm_configs(id),
    input_revision INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    state TEXT NOT NULL CHECK (state IN ('building','completed','failed')),
    actual_theta REAL CHECK (actual_theta >= 0),
    code_version TEXT NOT NULL
);

CREATE TABLE clusters (
    run_id TEXT NOT NULL REFERENCES analysis_runs(id),
    cluster_id INTEGER NOT NULL,
    cluster_key TEXT NOT NULL,
    e_agg REAL NOT NULL CHECK (e_agg BETWEEN 0 AND 1),
    f_agg REAL NOT NULL CHECK (f_agg BETWEEN 0 AND 1),
    n_norm REAL NOT NULL CHECK (n_norm BETWEEN 0 AND 1),
    v_agg REAL NOT NULL CHECK (v_agg >= 0),
    priority_score REAL NOT NULL CHECK (priority_score BETWEEN 0 AND 2),
    PRIMARY KEY (run_id, cluster_id),
    UNIQUE (run_id, cluster_key)
);

CREATE TABLE evidence_families (
    run_id TEXT NOT NULL,
    cluster_id INTEGER NOT NULL,
    family_id INTEGER NOT NULL,
    PRIMARY KEY (run_id, cluster_id, family_id),
    FOREIGN KEY (run_id, cluster_id) REFERENCES clusters(run_id, cluster_id)
);

-- Một dòng là một báo cáo trong một lần chạy, đồng thời là thành viên của một họ.
-- L/T/F/E/N/V là snapshot bất biến; Q_i là kết quả dẫn xuất theo cấu hình lần chạy.
CREATE TABLE analysis_members (
    run_id TEXT NOT NULL REFERENCES analysis_runs(id),
    report_id TEXT NOT NULL REFERENCES reports(id),
    cluster_id INTEGER NOT NULL,
    family_id INTEGER NOT NULL,
    lat REAL NOT NULL CHECK (lat BETWEEN -90 AND 90),
    lng REAL NOT NULL CHECK (lng BETWEEN -180 AND 180),
    observed_at TEXT NOT NULL,
    flood REAL NOT NULL CHECK (flood BETWEEN 0 AND 1),
    urgency REAL NOT NULL CHECK (urgency BETWEEN 0 AND 1),
    people_count REAL NOT NULL CHECK (people_count >= 0),
    vulnerability REAL NOT NULL CHECK (vulnerability >= 0),
    has_image INTEGER NOT NULL CHECK (has_image IN (0,1)),
    source_family TEXT,
    provenance_quality REAL CHECK (provenance_quality BETWEEN 0 AND 1),
    exact_fingerprint TEXT NOT NULL,
    n_corrob INTEGER NOT NULL CHECK (n_corrob >= 0),
    q_score REAL NOT NULL CHECK (q_score BETWEEN 0 AND 1),
    PRIMARY KEY (run_id, report_id),
    FOREIGN KEY (run_id, cluster_id, family_id)
        REFERENCES evidence_families(run_id, cluster_id, family_id)
);

CREATE INDEX idx_reports_updated_seq ON reports(updated_seq);
CREATE INDEX idx_reports_status ON reports(status);
CREATE INDEX idx_reports_received_at ON reports(server_received_at DESC);
CREATE INDEX idx_reports_first_received ON reports(first_received_at DESC);
CREATE INDEX idx_report_events_report ON report_events(report_id, id);
CREATE INDEX idx_sessions_operator ON sessions(operator_id);
CREATE INDEX idx_dedup_processed ON messages_dedup(processed_at);
CREATE INDEX idx_members_family ON analysis_members(run_id, cluster_id, family_id);
CREATE INDEX idx_members_report ON analysis_members(report_id, run_id);
CREATE INDEX idx_clusters_priority ON clusters(run_id, priority_score DESC);
