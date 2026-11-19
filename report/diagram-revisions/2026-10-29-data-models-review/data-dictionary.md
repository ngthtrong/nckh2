# Từ điển PDM đề xuất

Sinh trực tiếp từ `schema.sql`; đây là thiết kế để review, chưa áp dụng vào backend.

PK: khóa chính; FK: khóa ngoại; N: cho phép NULL. Default, CHECK, UNIQUE và FK ghép xem SQL.

## algorithm_configs

| Cột | Kiểu SQLite | PK | N | Mặc định |
|---|---|---|---|---|
| `id` | TEXT | 1 |  |  |
| `label` | TEXT |  |  |  |
| `created_at` | TEXT |  |  |  |
| `formula_version` | TEXT |  |  |  |
| `graph_mode` | TEXT |  |  |  |
| `community_algorithm` | TEXT |  |  |  |
| `sigma_geo_m` | REAL |  |  |  |
| `tau_t_min` | REAL |  |  |  |
| `tau_f` | REAL |  |  |  |
| `tau_e` | REAL |  |  |  |
| `alpha` | REAL |  |  |  |
| `beta` | REAL |  |  |  |
| `gamma` | REAL |  |  |  |
| `quantile_q` | REAL |  |  |  |
| `top_k` | INTEGER |  |  |  |
| `resolution` | REAL |  |  |  |
| `random_seed` | INTEGER |  |  |  |
| `q_b0` | REAL |  |  |  |
| `q_b1` | REAL |  |  |  |
| `q_b2` | REAL |  |  |  |
| `corrob_radius_m` | REAL |  |  |  |
| `corrob_window_min` | REAL |  |  |  |
| `omega_e` | REAL |  |  |  |
| `omega_f` | REAL |  |  |  |
| `omega_n` | REAL |  |  |  |
| `mu` | REAL |  |  |  |
| `v_scale` | REAL |  |  |  |
| `n_ref` | REAL |  |  |  |
| `n_claim_cap` | REAL |  |  |  |
| `v_cap` | REAL |  |  |  |
| `near_distance_m` | REAL |  |  |  |
| `near_time_min` | REAL |  |  |  |
| `near_f_abs` | REAL |  |  |  |
| `near_e_abs` | REAL |  |  |  |
| `near_n_floor` | REAL |  |  |  |
| `near_n_relative` | REAL |  |  |  |
| `near_v_abs` | REAL |  |  |  |
| `near_q_abs` | REAL |  |  |  |
| `require_same_source_family` | INTEGER |  |  |  |
| `require_same_image_state` | INTEGER |  |  |  |
| `lr_intercept` | REAL |  |  |  |
| `lr_coef_1` | REAL |  |  |  |
| `lr_coef_2` | REAL |  |  |  |
| `lr_coef_3` | REAL |  |  |  |
| `lr_coef_4` | REAL |  |  |  |
| `lr_coef_5` | REAL |  |  |  |
| `lr_threshold` | REAL |  |  |  |
| `lr_feature_order_json` | TEXT |  |  |  |
| `flood_mapping_json` | TEXT |  |  |  |

## analysis_members

| Cột | Kiểu SQLite | PK | N | Mặc định |
|---|---|---|---|---|
| `run_id` | TEXT | 1 |  |  |
| `report_id` | TEXT | 2 |  |  |
| `cluster_id` | INTEGER |  |  |  |
| `family_id` | INTEGER |  |  |  |
| `lat` | REAL |  |  |  |
| `lng` | REAL |  |  |  |
| `observed_at` | TEXT |  |  |  |
| `flood` | REAL |  |  |  |
| `urgency` | REAL |  |  |  |
| `people_count` | REAL |  |  |  |
| `vulnerability` | REAL |  |  |  |
| `has_image` | INTEGER |  |  |  |
| `source_family` | TEXT |  | N |  |
| `provenance_quality` | REAL |  | N |  |
| `exact_fingerprint` | TEXT |  |  |  |
| `n_corrob` | INTEGER |  |  |  |
| `q_score` | REAL |  |  |  |

- FK #0: `run_id` → `evidence_families.run_id`.

- FK #0: `cluster_id` → `evidence_families.cluster_id`.

- FK #0: `family_id` → `evidence_families.family_id`.

- FK #1: `report_id` → `reports.id`.

- FK #2: `run_id` → `analysis_runs.id`.

## analysis_runs

| Cột | Kiểu SQLite | PK | N | Mặc định |
|---|---|---|---|---|
| `id` | TEXT | 1 |  |  |
| `config_id` | TEXT |  |  |  |
| `input_revision` | INTEGER |  |  |  |
| `created_at` | TEXT |  |  |  |
| `completed_at` | TEXT |  | N |  |
| `state` | TEXT |  |  |  |
| `actual_theta` | REAL |  | N |  |
| `code_version` | TEXT |  |  |  |

- FK #0: `config_id` → `algorithm_configs.id`.

## clusters

| Cột | Kiểu SQLite | PK | N | Mặc định |
|---|---|---|---|---|
| `run_id` | TEXT | 1 |  |  |
| `cluster_id` | INTEGER | 2 |  |  |
| `cluster_key` | TEXT |  |  |  |
| `e_agg` | REAL |  |  |  |
| `f_agg` | REAL |  |  |  |
| `n_norm` | REAL |  |  |  |
| `v_agg` | REAL |  |  |  |
| `priority_score` | REAL |  |  |  |

- FK #0: `run_id` → `analysis_runs.id`.

## evidence_families

| Cột | Kiểu SQLite | PK | N | Mặc định |
|---|---|---|---|---|
| `run_id` | TEXT | 1 |  |  |
| `cluster_id` | INTEGER | 2 |  |  |
| `family_id` | INTEGER | 3 |  |  |

- FK #0: `run_id` → `clusters.run_id`.

- FK #0: `cluster_id` → `clusters.cluster_id`.

## messages_dedup

| Cột | Kiểu SQLite | PK | N | Mặc định |
|---|---|---|---|---|
| `message_id` | TEXT | 1 |  |  |
| `client_id` | TEXT |  |  |  |
| `sequence_number` | INTEGER |  |  |  |
| `operation_type` | TEXT |  |  |  |
| `payload_hash` | TEXT |  |  |  |
| `status` | TEXT |  |  |  |
| `error_code` | TEXT |  | N |  |
| `result_data` | TEXT |  | N |  |
| `created_at` | TEXT |  |  |  |
| `expires_at` | TEXT |  | N |  |
| `processed_at` | TEXT |  |  |  |
| `report_id` | TEXT |  | N |  |

- FK #0: `report_id` → `reports.id`.

## operators

| Cột | Kiểu SQLite | PK | N | Mặc định |
|---|---|---|---|---|
| `id` | INTEGER | 1 |  |  |
| `username` | TEXT |  |  |  |
| `display_name` | TEXT |  |  |  |
| `password_hash` | TEXT |  |  |  |
| `role` | TEXT |  |  | 'operator' |
| `active` | INTEGER |  |  | 1 |
| `must_change_password` | INTEGER |  |  | 0 |
| `created_at` | TEXT |  |  |  |
| `last_login_at` | TEXT |  | N |  |

## report_events

| Cột | Kiểu SQLite | PK | N | Mặc định |
|---|---|---|---|---|
| `id` | INTEGER | 1 |  |  |
| `report_id` | TEXT |  |  |  |
| `kind` | TEXT |  |  |  |
| `from_value` | TEXT |  | N |  |
| `to_value` | TEXT |  | N |  |
| `status_version` | INTEGER |  | N |  |
| `actor` | TEXT |  | N |  |
| `source` | TEXT |  |  |  |
| `note` | TEXT |  | N |  |
| `created_at` | TEXT |  |  |  |
| `operator_id` | INTEGER |  | N |  |

- FK #0: `operator_id` → `operators.id`.

- FK #1: `report_id` → `reports.id`.

## reports

| Cột | Kiểu SQLite | PK | N | Mặc định |
|---|---|---|---|---|
| `id` | TEXT | 1 |  |  |
| `server_received_at` | TEXT |  |  |  |
| `created_at` | TEXT |  | N |  |
| `lat` | REAL |  | N |  |
| `lng` | REAL |  | N |  |
| `trapped_count` | INTEGER |  | N | 0 |
| `injured_count` | INTEGER |  | N | 0 |
| `vulnerable_groups` | TEXT |  | N |  |
| `description` | TEXT |  | N |  |
| `ai_tags` | TEXT |  | N |  |
| `send_mode` | TEXT |  | N |  |
| `status` | TEXT |  |  | 'processing' |
| `status_version` | INTEGER |  |  | 1 |
| `image_filename` | TEXT |  | N |  |
| `image_local_path` | TEXT |  | N |  |
| `image_url` | TEXT |  | N |  |
| `image_sha256` | TEXT |  | N |  |
| `image_size_bytes` | INTEGER |  | N |  |
| `raw_payload` | TEXT |  |  |  |
| `first_received_at` | TEXT |  | N |  |
| `updated_seq` | INTEGER |  | N | 0 |
| `assigned_team_id` | INTEGER |  | N |  |
| `location_source` | TEXT |  | N |  |
| `close_reason` | TEXT |  | N |  |
| `status_updated_at` | TEXT |  | N |  |
| `owner_client_id` | TEXT |  | N |  |
| `source_id` | TEXT |  | N |  |
| `flood` | REAL |  | N |  |
| `urgency_lr` | REAL |  | N |  |
| `urgency` | REAL |  | N |  |
| `people_count` | REAL |  | N |  |
| `vulnerability` | REAL |  | N |  |
| `urgency_flags_json` | TEXT |  | N |  |
| `ai_model_version` | TEXT |  | N |  |
| `lr_model_version` | TEXT |  | N |  |
| `provenance_quality` | REAL |  | N |  |

- FK #0: `source_id` → `sources.id`.

- FK #1: `assigned_team_id` → `teams.id`.

## server_meta

| Cột | Kiểu SQLite | PK | N | Mặc định |
|---|---|---|---|---|
| `key` | TEXT | 1 |  |  |
| `value` | TEXT |  |  |  |

## sessions

| Cột | Kiểu SQLite | PK | N | Mặc định |
|---|---|---|---|---|
| `token_hash` | TEXT | 1 |  |  |
| `operator` | TEXT |  |  |  |
| `created_at` | TEXT |  |  |  |
| `expires_at` | TEXT |  |  |  |
| `operator_id` | INTEGER |  |  |  |

- FK #0: `operator_id` → `operators.id`.

## sources

| Cột | Kiểu SQLite | PK | N | Mặc định |
|---|---|---|---|---|
| `id` | TEXT | 1 |  |  |
| `kind` | TEXT |  |  |  |
| `source_family` | TEXT |  | N |  |
| `created_at` | TEXT |  |  |  |

## teams

| Cột | Kiểu SQLite | PK | N | Mặc định |
|---|---|---|---|---|
| `id` | INTEGER | 1 |  |  |
| `name` | TEXT |  |  |  |
| `phone` | TEXT |  | N |  |
| `members` | INTEGER |  | N |  |
| `note` | TEXT |  | N |  |
| `active` | INTEGER |  |  | 1 |
| `created_at` | TEXT |  |  |  |

