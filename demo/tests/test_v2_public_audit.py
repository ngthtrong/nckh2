from __future__ import annotations

import csv
import gzip
import json
import zipfile
from pathlib import Path

import pytest

from demo.v2.public_audit import (
    IDRISI_COMMIT,
    IDRISI_SPEC,
    NOAA_SPEC,
    UK_COLUMNS,
    UK_SPEC,
    PublicAuditError,
    SnapshotSpec,
    audit_idrisi,
    audit_noaa,
    audit_uk_ods,
    blocked_source_audits,
    main,
    sha256_file,
    verify_snapshot,
)


def _fixture_spec(path: Path, source_id: str) -> SnapshotSpec:
    return SnapshotSpec(
        source_id=source_id,
        local_filename=path.name,
        exact_url=f"https://example.invalid/snapshots/{path.name}",
        landing_url="https://example.invalid/",
        sha256=sha256_file(path),
    )


def _noaa_row(**overrides: str) -> dict[str, str]:
    row = {
        "EVENT_ID": "1",
        "STATE": "TEST STATE",
        "MONTH_NAME": "January",
        "EVENT_TYPE": "Flash Flood",
        "BEGIN_DATE_TIME": "01-JAN-24 00:00:00",
        "END_DATE_TIME": "01-JAN-24 05:00:00",
        "SOURCE": "Public",
        "BEGIN_LAT": "",
        "BEGIN_LON": "",
        "END_LAT": "",
        "END_LON": "",
        "FLOOD_CAUSE": "Heavy Rain",
        "EPISODE_NARRATIVE": "episode",
        "EVENT_NARRATIVE": "event",
        "INJURIES_DIRECT": "1",
        "INJURIES_INDIRECT": "0",
        "DEATHS_DIRECT": "0",
        "DEATHS_INDIRECT": "0",
        "DAMAGE_PROPERTY": "",
        "DAMAGE_CROPS": "0.00K",
    }
    row.update(overrides)
    return row


def _write_noaa_fixture(path: Path) -> SnapshotSpec:
    fieldnames = list(_noaa_row())
    rows = [
        _noaa_row(),
        _noaa_row(
            EVENT_ID="2",
            EVENT_TYPE="Flood",
            BEGIN_DATE_TIME="02-JAN-24 00:00:00",
            END_DATE_TIME="02-JAN-24 01:00:00",
            BEGIN_LAT="1",
            BEGIN_LON="2",
            END_LAT="1",
            END_LON="2",
            SOURCE="Emergency Manager",
            INJURIES_DIRECT="0",
            DEATHS_DIRECT="1",
        ),
        _noaa_row(
            EVENT_ID="3",
            EVENT_TYPE="Thunderstorm Wind",
            BEGIN_DATE_TIME="03-JAN-24 00:00:00",
            END_DATE_TIME="03-JAN-24 00:10:00",
        ),
    ]
    with gzip.open(path, "wt", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return _fixture_spec(path, "fixture.noaa")


def _ods_cell(value: str, *, repeat: int | None = None) -> str:
    repeat_attribute = (
        f' table:number-columns-repeated="{repeat}"' if repeat is not None else ""
    )
    if not value:
        return f"<table:table-cell{repeat_attribute}/>"
    return (
        f'<table:table-cell office:value-type="string"{repeat_attribute}>'
        f"<text:p>{value}</text:p></table:table-cell>"
    )


def _ods_row(values: list[str], *, repeat: int | None = None) -> str:
    repeat_attribute = f' table:number-rows-repeated="{repeat}"' if repeat else ""
    return (
        f"<table:table-row{repeat_attribute}>"
        + "".join(_ods_cell(value) for value in values)
        + "</table:table-row>"
    )


def _write_uk_fixture(path: Path) -> SnapshotSpec:
    first = [
        "Alpha FRS",
        "E1",
        "L1",
        "Area one",
        "2024/25",
        "Dwellings",
        "Flooding - Make safe",
        "1",
        "One",
        "0",
        "1",
        "No rescue",
        "None",
    ]
    second = [
        "Beta FRS",
        "E2",
        "Not known",
        "Not known",
        "2025/26",
        "River/canal",
        "Rescue or evacuation from water",
        "Not known",
        "Two",
        "Up to 5",
        "2",
        "Involved a Rescue",
        "Fatality/Casualty",
    ]
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<office:document-content
 xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
 xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">
 <office:body><office:spreadsheet>
  <table:table table:name="Cover_sheet">
   {_ods_row(["England, year ending March 2026", "Published: 22 July 2026"])}
  </table:table>
  <table:table table:name="Datasheet">
   {_ods_row(list(UK_COLUMNS))}
   {_ods_row(first, repeat=2)}
   {_ods_row(second)}
   <table:table-row table:number-rows-repeated="1048570">
    {_ods_cell('', repeat=1024)}
   </table:table-row>
  </table:table>
  <table:table table:name="config">
   {_ods_row(["Pubdate", "22 July 2026", "Datacut", "2026-05-12T00:00:00"])}
  </table:table>
 </office:spreadsheet></office:body>
</office:document-content>
"""
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("content.xml", content)
    return _fixture_spec(path, "fixture.uk")


def _jsonl(*records: dict[str, object]) -> str:
    return "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records)


def _gold_record(identifier: str, locations: list[dict[str, object]]) -> dict[str, object]:
    return {
        "tweet_id": identifier,
        "text": "aggregate-only fixture",
        "created_at": "Mon Jan 01 00:00:00 +0000 2024",
        "info_class": "request",
        "location_mentions": locations,
        "user_id": "not-exported",
    }


def _write_idrisi_fixture(path: Path) -> SnapshotSpec:
    root = f"IDRISI-{IDRISI_COMMIT}/LMR"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(f"{root}/README.md", "fixture")
        base = f"{root}/data/EN/gold-random-json/flood_event"
        archive.writestr(
            f"{base}/train.jsonl",
            _jsonl(
                _gold_record("1", []),
                _gold_record(
                    "2", [{"text": "Delta", "type": "CITY", "startIdx": 0}]
                ),
            ),
        )
        archive.writestr(f"{base}/dev.jsonl", _jsonl(_gold_record("3", [])))
        unlabeled = _gold_record("4", [])
        del unlabeled["location_mentions"]
        archive.writestr(f"{base}/test_unlabeled.jsonl", _jsonl(unlabeled))
        bilou = f"{root}/data/EN/gold-random-bilou/flood_event"
        archive.writestr(f"{bilou}/train.txt", "Delta B-CITY\n\n")
        archive.writestr(f"{bilou}/dev.txt", "water O\n\n")
        archive.writestr(
            f"{root}/data/AR/silver-random-json/arabic_flood.jsonl",
            _jsonl({"tweet_id": "5", "location_mentions": []}),
        )
    return _fixture_spec(path, "fixture.idrisi")


def test_checksum_verification_is_fail_closed(tmp_path: Path) -> None:
    snapshot = tmp_path / "snapshot.bin"
    snapshot.write_bytes(b"expected bytes")
    spec = _fixture_spec(snapshot, "fixture.checksum")
    snapshot.write_bytes(b"tampered bytes")

    with pytest.raises(PublicAuditError, match="SHA-256 mismatch"):
        verify_snapshot(snapshot, spec)


def test_noaa_audit_defines_subset_and_reports_missingness(tmp_path: Path) -> None:
    path = tmp_path / "noaa.csv.gz"
    spec = _write_noaa_fixture(path)

    audit = audit_noaa(path, spec=spec)

    assert audit["scope"]["all_event_rows"] == 3
    assert audit["scope"]["flood_subset_rows"] == 2
    assert audit["scope"]["flood_subset_definition"]["exact_included_values"] == [
        "Coastal Flood",
        "Flash Flood",
        "Flood",
        "Lakeshore Flood",
    ]
    assert audit["missingness"]["BEGIN_LAT"] == {"count": 1, "rate": 0.5}
    assert audit["descriptive_marginals"]["direct_plus_indirect_injuries"] == 1
    assert audit["descriptive_marginals"]["direct_plus_indirect_deaths"] == 1
    assert audit["descriptive_marginals"]["duration_minutes_linear_quantiles"][
        "p75"
    ] == 240.0


def test_uk_ods_audit_streams_repeats_and_preserves_unknowns(tmp_path: Path) -> None:
    path = tmp_path / "uk.ods"
    spec = _write_uk_fixture(path)

    audit = audit_uk_ods(path, spec=spec)

    assert audit["scope"]["expanded_incident_rows"] == 3
    assert audit["scope"]["unique_full_row_patterns"] == 2
    assert audit["scope"]["excess_indistinguishable_rows"] == 1
    assert audit["coverage"]["financial_year_min"] == "2024/25"
    assert audit["coverage"]["financial_year_max"] == "2025/26"
    assert audit["missingness"]["LSOA_CODE"]["not_known_sentinel"] == {
        "count": 1,
        "rate": 1 / 3,
    }
    assert audit["missingness"]["LSOA_CODE"]["blank"]["count"] == 0


def test_idrisi_inventory_distinguishes_unlabeled_from_labeled_test(
    tmp_path: Path,
) -> None:
    path = tmp_path / "idrisi.zip"
    spec = _write_idrisi_fixture(path)

    audit = audit_idrisi(path, spec=spec)

    test_audit = audit["test_partition_audit"]
    assert test_audit["labeled_test_partition_present"] is False
    assert test_audit["unlabeled_test_partition_present"] is True
    assert test_audit["unlabeled_test_file_count"] == 1
    assert test_audit["unlabeled_test_records_with_location_mentions_key"] == 0

    train = next(
        row
        for row in audit["partition_inventory"]
        if row["release"] == "gold-random-json" and row["partition"] == "train"
    )
    assert train["jsonl_records"] == 2
    assert train["jsonl_missingness"]["location_mentions"]["count"] == 0
    assert train["jsonl_empty_values"]["location_mentions"]["count"] == 1
    assert train["jsonl_user_id_present"] == 2


def test_blocked_sources_do_not_invent_snapshots_or_counts() -> None:
    blocked = blocked_source_audits()
    assert {row["source_id"] for row in blocked} == {
        "source.trec_is",
        "source.crisisfacts",
    }
    assert all(row["audit_status"] == "blocked" for row in blocked)
    assert all(row["local_snapshot_present"] is False for row in blocked)
    assert all(row["sha256"] is None for row in blocked)
    assert all(row["data_or_counts_imputed"] is False for row in blocked)
    assert all(row["usable_as_evidence"] is False for row in blocked)


def test_cli_rejects_unpinned_bytes_before_parsing(tmp_path: Path) -> None:
    wrong = tmp_path / "wrong.bin"
    wrong.write_bytes(b"not a pinned snapshot")

    with pytest.raises(SystemExit) as error:
        main(
            [
                "reproduce_external",
                "--noaa",
                str(wrong),
                "--uk",
                str(wrong),
                "--idrisi",
                str(wrong),
            ]
        )
    assert error.value.code == 2


def test_pinned_snapshot_identifiers_are_exact() -> None:
    assert NOAA_SPEC.sha256 == (
        "2070b83eccab041b36360ab73645b9a249c3eefc5b92b5b3fc0cbba4d9fcc09c"
    )
    assert NOAA_SPEC.exact_url.endswith(
        "StormEvents_details-ftp_v1.0_d2024_c20260728.csv.gz"
    )
    assert UK_SPEC.sha256 == (
        "8e140a4f3660e3afbee72c1028ece391ddda6b44dcd26f9d9cea2f4d5922f137"
    )
    assert UK_SPEC.exact_url.endswith("Flooding_and_water_rescue_incidents_dataset.ods")
    assert IDRISI_SPEC.sha256 == (
        "b8d2113f37f76ae6e7112f715d374daf1ca11a170fe7344a0c0caf6eed8a65f2"
    )
    assert IDRISI_COMMIT in IDRISI_SPEC.exact_url


def test_committed_anchor_records_only_bounded_external_evidence() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    anchor = json.loads(
        (repository_root / "revision/v2/public_anchor.json").read_text(
            encoding="utf-8"
        )
    )

    noaa = anchor["audited_sources"]["source.noaa_storm_events"]
    uk = anchor["audited_sources"]["source.uk_water_rescue"]
    idrisi = anchor["audited_sources"]["source.idrisi_re"]
    assert noaa["scope"]["all_event_rows"] == 69_801
    assert noaa["scope"]["flood_subset_rows"] == 7_516
    assert noaa["descriptive_marginals"][
        "duration_minutes_linear_quantiles"
    ]["p75"] == 300.0
    assert uk["scope"]["expanded_incident_rows"] == 266_767
    assert idrisi["test_partition_audit"]["labeled_test_partition_present"] is False
    assert idrisi["test_partition_audit"]["unlabeled_test_file_count"] == 19

    mapping = anchor["anchor_mapping"]
    assert mapping["generator_fit"]["performed"] is False
    assert mapping["uk_noaa_unit_compatibility"][
        "compatible_for_joint_parameter_estimation"
    ] is False
    assert anchor["seed_safety"]["generator_invoked"] is False
    assert anchor["seed_safety"]["confirmation_seeds_generated"] is False
