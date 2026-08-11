"""Reproducible, aggregate-only audit of pinned public-data snapshots.

This module is deliberately isolated from the v2 generator and experiment
pipeline.  It reads three byte-for-byte pinned public snapshots, verifies each
SHA-256 digest *before* parsing, and emits descriptive aggregate evidence.  It
does not tune parameters, construct reports, allocate seeds, or expose raw
social-media records.

Reproduce the committed audit from the repository root with::

    python -m demo.v2.public_audit reproduce_external \
      --noaa /tmp/nckh2-public-audit/noaa_storm_events_2024.csv.gz \
      --uk /tmp/nckh2-public-audit/uk_flooding_water_rescue.ods \
      --idrisi /tmp/nckh2-public-audit/idrisi_3dfd62d.zip \
      --output revision/v2/public_anchor.json

Only Python's standard library is used.  In particular, ODS input is streamed
directly from ``content.xml`` in the ZIP container rather than loaded through a
spreadsheet library.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import os
import tempfile
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, BinaryIO, Iterator, Mapping, Sequence
from xml.etree import ElementTree as ET


AUDIT_DATE = "2026-08-11"
SCHEMA_VERSION = "v2.public-anchor.1"
IDRISI_COMMIT = "3dfd62d867b23b7143999ffb29fe137d6ca5989b"


class PublicAuditError(RuntimeError):
    """Raised when a snapshot or its structure fails a closed audit gate."""


@dataclass(frozen=True)
class SnapshotSpec:
    """Immutable identity and provenance for one audited byte snapshot."""

    source_id: str
    local_filename: str
    exact_url: str
    landing_url: str
    sha256: str

    def __post_init__(self) -> None:
        digest = self.sha256.lower()
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("sha256 must be exactly 64 lowercase hexadecimal characters")
        object.__setattr__(self, "sha256", digest)


NOAA_SPEC = SnapshotSpec(
    source_id="source.noaa_storm_events",
    local_filename="noaa_storm_events_2024.csv.gz",
    exact_url=(
        "https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/"
        "StormEvents_details-ftp_v1.0_d2024_c20260728.csv.gz"
    ),
    landing_url="https://www.ncei.noaa.gov/stormevents/ftp.jsp",
    sha256="2070b83eccab041b36360ab73645b9a249c3eefc5b92b5b3fc0cbba4d9fcc09c",
)

UK_SPEC = SnapshotSpec(
    source_id="source.uk_water_rescue",
    local_filename="uk_flooding_water_rescue.ods",
    exact_url=(
        "https://assets.publishing.service.gov.uk/media/"
        "6a5e779dc7c34404041b4661/"
        "Flooding_and_water_rescue_incidents_dataset.ods"
    ),
    landing_url=(
        "https://www.gov.uk/government/statistics/"
        "fire-statistics-incident-level-datasets"
    ),
    sha256="8e140a4f3660e3afbee72c1028ece391ddda6b44dcd26f9d9cea2f4d5922f137",
)

IDRISI_SPEC = SnapshotSpec(
    source_id="source.idrisi_re",
    local_filename="idrisi_3dfd62d.zip",
    exact_url=f"https://github.com/rsuwaileh/IDRISI/archive/{IDRISI_COMMIT}.zip",
    landing_url=f"https://github.com/rsuwaileh/IDRISI/commit/{IDRISI_COMMIT}",
    sha256="b8d2113f37f76ae6e7112f715d374daf1ca11a170fe7344a0c0caf6eed8a65f2",
)


FLOOD_EVENT_TYPES = frozenset(
    {"Flash Flood", "Flood", "Coastal Flood", "Lakeshore Flood"}
)
NOAA_MISSINGNESS_FIELDS = (
    "BEGIN_LAT",
    "BEGIN_LON",
    "END_LAT",
    "END_LON",
    "FLOOD_CAUSE",
    "EPISODE_NARRATIVE",
    "EVENT_NARRATIVE",
    "INJURIES_DIRECT",
    "INJURIES_INDIRECT",
    "DEATHS_DIRECT",
    "DEATHS_INDIRECT",
    "DAMAGE_PROPERTY",
    "DAMAGE_CROPS",
)
NOAA_REQUIRED_FIELDS = frozenset(
    {
        "EVENT_ID",
        "STATE",
        "MONTH_NAME",
        "EVENT_TYPE",
        "BEGIN_DATE_TIME",
        "END_DATE_TIME",
        "SOURCE",
        *NOAA_MISSINGNESS_FIELDS,
    }
)

UK_COLUMNS = (
    "FRS_TERRITORY",
    "E_CODE_TERRITORY",
    "LSOA_CODE",
    "LSOA_DESCRIPTION",
    "FINANCIAL_YEAR",
    "LOCATION_TYPE",
    "INCIDENT_TYPE",
    "EVACUATIONS",
    "VEHICLES",
    "VEHICLES_CODE",
    "EVACUATIONS_CODE",
    "RESCUES",
    "FATALITY_CASUALTY",
)

_OFFICE_NS = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"
_TABLE_NS = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"
_TEXT_NS = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
_TABLE = f"{{{_TABLE_NS}}}table"
_ROW = f"{{{_TABLE_NS}}}table-row"
_CELL = f"{{{_TABLE_NS}}}table-cell"
_COVERED_CELL = f"{{{_TABLE_NS}}}covered-table-cell"
_TABLE_NAME = f"{{{_TABLE_NS}}}name"
_ROW_REPEAT = f"{{{_TABLE_NS}}}number-rows-repeated"
_COLUMN_REPEAT = f"{{{_TABLE_NS}}}number-columns-repeated"


def sha256_file(path: str | os.PathLike[str], *, chunk_size: int = 1 << 20) -> str:
    """Return a streaming SHA-256 digest for ``path``."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def verify_snapshot(
    path: str | os.PathLike[str], spec: SnapshotSpec
) -> dict[str, Any]:
    """Fail closed unless ``path`` is a regular file with the pinned digest."""

    snapshot = Path(path)
    if not snapshot.is_file():
        raise PublicAuditError(f"missing regular-file snapshot: {snapshot}")
    observed = sha256_file(snapshot)
    if observed != spec.sha256:
        raise PublicAuditError(
            f"SHA-256 mismatch for {spec.source_id}: expected {spec.sha256}, "
            f"observed {observed}"
        )
    return {
        "local_filename": spec.local_filename,
        "byte_size": snapshot.stat().st_size,
        "sha256": observed,
        "checksum_verified_before_parse": True,
        "exact_snapshot_url": spec.exact_url,
        "landing_url": spec.landing_url,
    }


def _count_rate(count: int, denominator: int) -> dict[str, int | float | None]:
    return {
        "count": count,
        "rate": count / denominator if denominator else None,
    }


def _counter_rows(counter: Mapping[str, int], denominator: int) -> list[dict[str, Any]]:
    return [
        {"value": value, "count": count, "rate": count / denominator}
        for value, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    ]


def _linear_quantile(sorted_values: Sequence[float], probability: float) -> float:
    if not sorted_values:
        raise PublicAuditError("cannot calculate a quantile of an empty sequence")
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must be in [0, 1]")
    position = (len(sorted_values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(sorted_values[lower])
    fraction = position - lower
    # Rounding suppresses irrelevant binary-representation tails (for example,
    # 16483.20000000004) while retaining sub-minute precision if it exists.
    return round(
        float(
            sorted_values[lower]
            + fraction * (sorted_values[upper] - sorted_values[lower])
        ),
        9,
    )


def _parse_noaa_datetime(value: str) -> datetime:
    try:
        return datetime.strptime(value.strip(), "%d-%b-%y %H:%M:%S")
    except ValueError as exc:
        raise PublicAuditError(f"invalid NOAA date-time {value!r}") from exc


def _parse_nonnegative_integer(value: str, field: str) -> int:
    text = value.strip()
    try:
        parsed = int(text)
    except ValueError as exc:
        raise PublicAuditError(f"invalid integer in NOAA {field}: {value!r}") from exc
    if parsed < 0:
        raise PublicAuditError(f"negative integer in NOAA {field}: {parsed}")
    return parsed


def audit_noaa(
    path: str | os.PathLike[str], *, spec: SnapshotSpec = NOAA_SPEC
) -> dict[str, Any]:
    """Audit the pinned NOAA detail CSV and its explicitly defined flood subset."""

    snapshot = verify_snapshot(path, spec)
    total_rows = 0
    event_ids: Counter[str] = Counter()
    event_types: Counter[str] = Counter()
    flood_types: Counter[str] = Counter()
    flood_states: Counter[str] = Counter()
    flood_months: Counter[str] = Counter()
    flood_sources: Counter[str] = Counter()
    missing = Counter({field: 0 for field in NOAA_MISSINGNESS_FIELDS})
    flood_rows = 0
    begin_min: datetime | None = None
    begin_max: datetime | None = None
    durations: list[float] = []
    negative_durations = 0
    injury_total = 0
    death_total = 0

    try:
        stream = gzip.open(path, "rt", encoding="utf-8-sig", newline="")
        with stream:
            reader = csv.DictReader(stream)
            fields = set(reader.fieldnames or ())
            absent = sorted(NOAA_REQUIRED_FIELDS - fields)
            if absent:
                raise PublicAuditError(f"NOAA CSV is missing required columns: {absent}")
            for row in reader:
                total_rows += 1
                event_id = row["EVENT_ID"].strip()
                if not event_id:
                    raise PublicAuditError(f"NOAA row {total_rows} has blank EVENT_ID")
                event_ids[event_id] += 1
                event_type = row["EVENT_TYPE"].strip()
                event_types[event_type] += 1
                if event_type not in FLOOD_EVENT_TYPES:
                    continue

                flood_rows += 1
                flood_types[event_type] += 1
                flood_states[row["STATE"].strip() or "(blank)"] += 1
                flood_months[row["MONTH_NAME"].strip() or "(blank)"] += 1
                flood_sources[row["SOURCE"].strip() or "(blank)"] += 1
                for field in NOAA_MISSINGNESS_FIELDS:
                    if not row[field].strip():
                        missing[field] += 1

                begin = _parse_noaa_datetime(row["BEGIN_DATE_TIME"])
                end = _parse_noaa_datetime(row["END_DATE_TIME"])
                begin_min = begin if begin_min is None else min(begin_min, begin)
                begin_max = begin if begin_max is None else max(begin_max, begin)
                duration = (end - begin).total_seconds() / 60.0
                if duration < 0:
                    negative_durations += 1
                else:
                    durations.append(duration)

                injury_total += _parse_nonnegative_integer(
                    row["INJURIES_DIRECT"], "INJURIES_DIRECT"
                )
                injury_total += _parse_nonnegative_integer(
                    row["INJURIES_INDIRECT"], "INJURIES_INDIRECT"
                )
                death_total += _parse_nonnegative_integer(
                    row["DEATHS_DIRECT"], "DEATHS_DIRECT"
                )
                death_total += _parse_nonnegative_integer(
                    row["DEATHS_INDIRECT"], "DEATHS_INDIRECT"
                )
    except (OSError, EOFError, csv.Error) as exc:
        raise PublicAuditError(f"cannot parse NOAA gzip CSV: {exc}") from exc

    if flood_rows == 0 or begin_min is None or begin_max is None:
        raise PublicAuditError("NOAA snapshot contains no rows in the declared flood subset")
    if negative_durations:
        raise PublicAuditError(
            f"NOAA flood subset contains {negative_durations} negative durations"
        )

    durations.sort()
    duration_quantiles = {
        "min": durations[0],
        "p25": _linear_quantile(durations, 0.25),
        "p50": _linear_quantile(durations, 0.50),
        "p75": _linear_quantile(durations, 0.75),
        "p90": _linear_quantile(durations, 0.90),
        "p95": _linear_quantile(durations, 0.95),
        "p99": _linear_quantile(durations, 0.99),
        "max": durations[-1],
    }
    within_300 = sum(duration <= 300.0 for duration in durations)
    duplicate_rows = sum(count - 1 for count in event_ids.values() if count > 1)

    return {
        "source_id": spec.source_id,
        "audit_status": "pass",
        "snapshot": snapshot,
        "scope": {
            "source_grain": "one NOAA storm-event detail row",
            "all_event_rows": total_rows,
            "unique_event_ids": len(event_ids),
            "excess_rows_sharing_event_id": duplicate_rows,
            "flood_subset_definition": {
                "column": "EVENT_TYPE",
                "exact_included_values": sorted(FLOOD_EVENT_TYPES),
            },
            "flood_subset_rows": flood_rows,
            "flood_subset_rate": flood_rows / total_rows,
        },
        "coverage": {
            "begin_date_time_min_local": begin_min.isoformat(sep=" "),
            "begin_date_time_max_local": begin_max.isoformat(sep=" "),
            "date_time_note": "NOAA local event time; CZ_TIMEZONE varies by row",
            "states_or_territories": len(flood_states),
            "duration_rows": len(durations),
            "negative_duration_rows": negative_durations,
        },
        "missingness": {
            field: _count_rate(missing[field], flood_rows)
            for field in NOAA_MISSINGNESS_FIELDS
        },
        "descriptive_marginals": {
            "flood_event_type": _counter_rows(flood_types, flood_rows),
            "state_or_territory": _counter_rows(flood_states, flood_rows),
            "month_name": _counter_rows(flood_months, flood_rows),
            "source": _counter_rows(flood_sources, flood_rows),
            "duration_minutes_linear_quantiles": duration_quantiles,
            "duration_at_most_300_minutes": _count_rate(within_300, flood_rows),
            "direct_plus_indirect_injuries": injury_total,
            "direct_plus_indirect_deaths": death_total,
        },
        "claim_limits": [
            "NOAA rows are weather events, not repeated rescue reports or a physical-incident clustering partition.",
            "The snapshot has no human need or pre-dispatch priority label.",
            "Durations and outcomes are descriptive and were not used to fit the synthetic generator.",
        ],
    }


def _ods_cell_text(cell: ET.Element) -> str:
    value_type = cell.get(f"{{{_OFFICE_NS}}}value-type")
    if value_type == "string":
        explicit = cell.get(f"{{{_OFFICE_NS}}}string-value")
        if explicit is not None:
            return explicit.strip()
    for attribute in ("date-value", "time-value", "boolean-value", "value"):
        explicit = cell.get(f"{{{_OFFICE_NS}}}{attribute}")
        if explicit is not None:
            return explicit.strip()
    paragraphs = []
    for paragraph in cell.iter(f"{{{_TEXT_NS}}}p"):
        text = "".join(paragraph.itertext()).strip()
        if text:
            paragraphs.append(text)
    return "\n".join(paragraphs)


def _ods_row_values(row: ET.Element, *, max_columns: int = 256) -> list[str]:
    values: list[str] = []
    for cell in row:
        if cell.tag not in {_CELL, _COVERED_CELL}:
            continue
        repeat_text = cell.get(_COLUMN_REPEAT, "1")
        try:
            repeat = int(repeat_text)
        except ValueError as exc:
            raise PublicAuditError(f"invalid ODS column repeat: {repeat_text!r}") from exc
        if repeat <= 0:
            raise PublicAuditError(f"non-positive ODS column repeat: {repeat}")
        value = "" if cell.tag == _COVERED_CELL else _ods_cell_text(cell)
        remaining = max_columns - len(values)
        if remaining <= 0:
            if value:
                raise PublicAuditError("ODS row exceeds the audit column bound")
            continue
        values.extend([value] * min(repeat, remaining))
        if repeat > remaining and value:
            raise PublicAuditError("non-empty ODS repeated cell exceeds audit column bound")
    while values and values[-1] == "":
        values.pop()
    return values


def iter_ods_rows(path: str | os.PathLike[str]) -> Iterator[tuple[str, list[str], int]]:
    """Yield non-empty ODS rows as ``(sheet, values, repeat)`` with bounded memory."""

    try:
        archive = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as exc:
        raise PublicAuditError(f"cannot open ODS ZIP container: {exc}") from exc

    with archive:
        try:
            content: BinaryIO = archive.open("content.xml")
        except KeyError as exc:
            raise PublicAuditError("ODS archive has no content.xml") from exc
        with content:
            stack: list[ET.Element] = []
            current_table: str | None = None
            try:
                for event, element in ET.iterparse(content, events=("start", "end")):
                    if event == "start":
                        stack.append(element)
                        if element.tag == _TABLE:
                            current_table = element.get(_TABLE_NAME, "")
                        continue

                    if element.tag == _ROW and current_table is not None:
                        values = _ods_row_values(element)
                        repeat_text = element.get(_ROW_REPEAT, "1")
                        try:
                            repeat = int(repeat_text)
                        except ValueError as exc:
                            raise PublicAuditError(
                                f"invalid ODS row repeat: {repeat_text!r}"
                            ) from exc
                        if repeat <= 0:
                            raise PublicAuditError(
                                f"non-positive ODS row repeat: {repeat}"
                            )
                        if values:
                            yield current_table, values, repeat

                        element.clear()
                        if len(stack) >= 2:
                            try:
                                stack[-2].remove(element)
                            except ValueError:
                                pass
                    elif element.tag == _TABLE:
                        current_table = None
                        element.clear()

                    if not stack or stack[-1] is not element:
                        raise PublicAuditError("unexpected ODS XML nesting")
                    stack.pop()
            except ET.ParseError as exc:
                raise PublicAuditError(f"invalid ODS content.xml: {exc}") from exc


def audit_uk_ods(
    path: str | os.PathLike[str], *, spec: SnapshotSpec = UK_SPEC
) -> dict[str, Any]:
    """Audit the England flooding/water-rescue ODS using weighted row repeats."""

    snapshot = verify_snapshot(path, spec)
    header_seen = False
    incident_rows = 0
    row_patterns: Counter[tuple[str, ...]] = Counter()
    column_counters: dict[str, Counter[str]] = {
        column: Counter() for column in UK_COLUMNS
    }
    blank_counts: Counter[str] = Counter()
    not_known_counts: Counter[str] = Counter()
    cover_values: set[str] = set()
    config_values: set[str] = set()
    sheet_names: set[str] = set()

    for sheet, values, repeat in iter_ods_rows(path):
        sheet_names.add(sheet)
        sheet_key = sheet.strip().lower()
        if sheet_key == "cover_sheet":
            cover_values.update(value for value in values if value)
            continue
        if sheet_key == "config":
            config_values.update(value for value in values if value)
            continue
        if sheet_key != "datasheet":
            continue

        if not header_seen:
            observed_header = tuple(values)
            if observed_header != UK_COLUMNS:
                raise PublicAuditError(
                    "unexpected UK Datasheet header: " + repr(observed_header)
                )
            if repeat != 1:
                raise PublicAuditError("UK Datasheet header is unexpectedly repeated")
            header_seen = True
            continue

        if len(values) > len(UK_COLUMNS):
            raise PublicAuditError(
                f"UK Datasheet row has {len(values)} columns, expected at most "
                f"{len(UK_COLUMNS)}"
            )
        padded = tuple(values + [""] * (len(UK_COLUMNS) - len(values)))
        incident_rows += repeat
        row_patterns[padded] += repeat
        for column, value in zip(UK_COLUMNS, padded):
            column_counters[column][value] += repeat
            if value == "":
                blank_counts[column] += repeat
            if value.casefold() == "not known":
                not_known_counts[column] += repeat

    if not header_seen:
        raise PublicAuditError("UK ODS has no Datasheet header")
    if incident_rows == 0:
        raise PublicAuditError("UK ODS Datasheet has no incident rows")

    excess_identical = sum(count - 1 for count in row_patterns.values())
    financial_years = column_counters["FINANCIAL_YEAR"]
    rescues = column_counters["RESCUES"]
    casualties = column_counters["FATALITY_CASUALTY"]

    publication_markers = sorted(
        value
        for value in cover_values | config_values
        if "2026" in value or "22 July" in value or "12-May-26" in value
    )

    return {
        "source_id": spec.source_id,
        "audit_status": "pass",
        "snapshot": snapshot,
        "scope": {
            "source_grain": "one public row per attended fire-and-rescue incident",
            "expanded_incident_rows": incident_rows,
            "unique_full_row_patterns": len(row_patterns),
            "excess_indistinguishable_rows": excess_identical,
            "indistinguishability_note": (
                "The public table has no incident identifier; byte-identical rows "
                "cannot be classified as duplicate records versus distinct incidents."
            ),
            "datasheet_columns": list(UK_COLUMNS),
        },
        "coverage": {
            "sheets": sorted(sheet_names),
            "financial_year_min": min(financial_years),
            "financial_year_max": max(financial_years),
            "financial_year_count": len(financial_years),
            "fire_and_rescue_territories": len(column_counters["FRS_TERRITORY"]),
            "publication_metadata_markers": publication_markers,
        },
        "missingness": {
            column: {
                "blank": _count_rate(blank_counts[column], incident_rows),
                "not_known_sentinel": _count_rate(
                    not_known_counts[column], incident_rows
                ),
            }
            for column in UK_COLUMNS
        },
        "descriptive_marginals": {
            "financial_year": _counter_rows(financial_years, incident_rows),
            "location_type": _counter_rows(
                column_counters["LOCATION_TYPE"], incident_rows
            ),
            "incident_type": _counter_rows(
                column_counters["INCIDENT_TYPE"], incident_rows
            ),
            "evacuations_published_band": _counter_rows(
                column_counters["EVACUATIONS"], incident_rows
            ),
            "vehicles_published_band": _counter_rows(
                column_counters["VEHICLES_CODE"], incident_rows
            ),
            "rescue_indicator": _counter_rows(rescues, incident_rows),
            "fatality_or_casualty_indicator": _counter_rows(
                casualties, incident_rows
            ),
        },
        "claim_limits": [
            "The public unit is an attended incident, not a stream of reports to cluster.",
            "Time is only a financial year and response/outcome variables are binary or banded.",
            "The England administrative schema is not commensurate with NOAA event durations or synthetic rescue-report fields.",
            "These marginals are descriptive and were not used to fit the synthetic generator.",
        ],
    }


def _json_record_missing(record: Mapping[str, Any], key: str) -> bool:
    """Treat absent/null as missing, but preserve valid empty-label negatives."""

    return key not in record or record[key] is None


def _json_record_empty(record: Mapping[str, Any], key: str) -> bool:
    return key in record and record[key] in ("", [], {})


def _idrisi_partition(path_parts: Sequence[str]) -> tuple[str, str, str, str] | None:
    """Return ``(language, release, event, partition)`` for an LMR data file."""

    try:
        marker = path_parts.index("data")
    except ValueError:
        return None
    suffix = path_parts[marker + 1 :]
    if len(suffix) == 4:
        language, release, event, filename = suffix
        return language, release, event, Path(filename).stem
    if len(suffix) == 3:
        language, release, filename = suffix
        return language, release, Path(filename).stem, "unpartitioned"
    return None


def _profile_idrisi_jsonl(
    archive: zipfile.ZipFile,
    info: zipfile.ZipInfo,
) -> dict[str, Any]:
    records = 0
    malformed = 0
    missing = Counter(
        {
            "tweet_id": 0,
            "text": 0,
            "created_at": 0,
            "information_class": 0,
            "location_mentions": 0,
        }
    )
    empty = Counter(
        {
            "tweet_id": 0,
            "text": 0,
            "created_at": 0,
            "information_class": 0,
            "location_mentions": 0,
        }
    )
    user_id_present = 0
    with archive.open(info) as stream:
        for raw_line in stream:
            if not raw_line.strip():
                continue
            records += 1
            try:
                value = json.loads(raw_line)
            except (UnicodeDecodeError, json.JSONDecodeError):
                malformed += 1
                continue
            if not isinstance(value, dict):
                malformed += 1
                continue
            if _json_record_missing(value, "tweet_id"):
                missing["tweet_id"] += 1
            elif _json_record_empty(value, "tweet_id"):
                empty["tweet_id"] += 1
            if _json_record_missing(value, "text"):
                missing["text"] += 1
            elif _json_record_empty(value, "text"):
                empty["text"] += 1
            if _json_record_missing(value, "created_at"):
                missing["created_at"] += 1
            elif _json_record_empty(value, "created_at"):
                empty["created_at"] += 1
            information_values = [
                value[key]
                for key in ("info_class", "humAID_class")
                if key in value and value[key] is not None
            ]
            if not information_values:
                missing["information_class"] += 1
            elif all(item in ("", [], {}) for item in information_values):
                empty["information_class"] += 1
            if _json_record_missing(value, "location_mentions"):
                missing["location_mentions"] += 1
            elif _json_record_empty(value, "location_mentions"):
                empty["location_mentions"] += 1
            if "user_id" in value and value["user_id"] not in (None, ""):
                user_id_present += 1
    return {
        "records": records,
        "malformed_json_records": malformed,
        "missing": missing,
        "empty": empty,
        "user_id_present": user_id_present,
    }


def audit_idrisi(
    path: str | os.PathLike[str], *, spec: SnapshotSpec = IDRISI_SPEC
) -> dict[str, Any]:
    """Inventory the pinned IDRISI release without exporting any raw records."""

    snapshot = verify_snapshot(path, spec)
    try:
        archive = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as exc:
        raise PublicAuditError(f"cannot open IDRISI ZIP: {exc}") from exc

    inventory: dict[tuple[str, str, str], dict[str, Any]] = defaultdict(
        lambda: {
            "files": 0,
            "uncompressed_bytes": 0,
            "events": set(),
            "jsonl_records": 0,
            "malformed_json_records": 0,
            "jsonl_missing": Counter(),
            "jsonl_empty": Counter(),
            "jsonl_user_id_present": 0,
        }
    )
    regular_files = 0
    total_uncompressed = 0
    total_compressed = 0
    lmr_files = 0
    lmr_uncompressed = 0
    extension_counts: Counter[str] = Counter()
    roots: set[str] = set()
    labeled_test_files: list[str] = []
    unlabeled_test_files: list[str] = []

    with archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            regular_files += 1
            total_uncompressed += info.file_size
            total_compressed += info.compress_size
            parts = Path(info.filename).parts
            if not parts:
                raise PublicAuditError("IDRISI ZIP contains an empty path")
            roots.add(parts[0])
            if any(part == ".." for part in parts) or info.filename.startswith("/"):
                raise PublicAuditError(f"unsafe IDRISI archive path: {info.filename}")
            if "LMR" not in parts:
                continue

            lmr_files += 1
            lmr_uncompressed += info.file_size
            extension_counts[Path(info.filename).suffix.lower().lstrip(".") or "none"] += 1
            classified = _idrisi_partition(parts)
            if classified is None:
                continue
            language, release, event, partition = classified
            key = (language, release, partition)
            entry = inventory[key]
            entry["files"] += 1
            entry["uncompressed_bytes"] += info.file_size
            entry["events"].add(event)

            partition_lower = partition.casefold()
            if partition_lower.startswith("test"):
                if "unlabeled" in partition_lower:
                    unlabeled_test_files.append(info.filename)
                else:
                    labeled_test_files.append(info.filename)

            if Path(info.filename).suffix.lower() == ".jsonl":
                profile = _profile_idrisi_jsonl(archive, info)
                entry["jsonl_records"] += profile["records"]
                entry["malformed_json_records"] += profile[
                    "malformed_json_records"
                ]
                entry["jsonl_missing"].update(profile["missing"])
                entry["jsonl_empty"].update(profile["empty"])
                entry["jsonl_user_id_present"] += profile["user_id_present"]

    expected_root = f"IDRISI-{IDRISI_COMMIT}"
    if roots != {expected_root}:
        raise PublicAuditError(
            f"IDRISI archive root mismatch: expected {expected_root!r}, "
            f"observed {sorted(roots)!r}"
        )

    inventory_rows: list[dict[str, Any]] = []
    for (language, release, partition), entry in sorted(inventory.items()):
        records = entry["jsonl_records"]
        jsonl_missing = {
            field: _count_rate(count, records)
            for field, count in sorted(entry["jsonl_missing"].items())
        }
        jsonl_empty = {
            field: _count_rate(count, records)
            for field, count in sorted(entry["jsonl_empty"].items())
        }
        inventory_rows.append(
            {
                "language": language,
                "release": release,
                "partition": partition,
                "event_files": len(entry["events"]),
                "files": entry["files"],
                "uncompressed_bytes": entry["uncompressed_bytes"],
                "jsonl_records": records if records else None,
                "malformed_json_records": (
                    entry["malformed_json_records"] if records else None
                ),
                "jsonl_missingness": jsonl_missing if records else None,
                "jsonl_empty_values": jsonl_empty if records else None,
                "jsonl_user_id_present": (
                    entry["jsonl_user_id_present"] if records else None
                ),
            }
        )

    unlabeled_label_keys = 0
    for row in inventory_rows:
        if row["partition"] != "test_unlabeled" or not row["jsonl_records"]:
            continue
        missing_locations = row["jsonl_missingness"]["location_mentions"]["count"]
        unlabeled_label_keys += row["jsonl_records"] - missing_locations

    return {
        "source_id": spec.source_id,
        "audit_status": "pass",
        "snapshot": {
            **snapshot,
            "pinned_commit": IDRISI_COMMIT,
            "exact_commit_url": (
                f"https://github.com/rsuwaileh/IDRISI/commit/{IDRISI_COMMIT}"
            ),
        },
        "scope": {
            "archive_root": expected_root,
            "regular_files": regular_files,
            "total_uncompressed_bytes": total_uncompressed,
            "total_compressed_entry_bytes": total_compressed,
            "lmr_regular_files": lmr_files,
            "lmr_uncompressed_bytes": lmr_uncompressed,
            "lmr_extension_counts": dict(sorted(extension_counts.items())),
        },
        "partition_inventory": inventory_rows,
        "test_partition_audit": {
            "labeled_test_partition_present": bool(labeled_test_files),
            "labeled_test_file_count": len(labeled_test_files),
            "unlabeled_test_partition_present": bool(unlabeled_test_files),
            "unlabeled_test_file_count": len(unlabeled_test_files),
            "unlabeled_test_records_with_location_mentions_key": unlabeled_label_keys,
            "interpretation": (
                "No labeled test partition is released. The snapshot does contain "
                "English gold-random JSONL files explicitly named "
                "test_unlabeled.jsonl; these are not evaluation labels."
            ),
        },
        "coverage": {
            "languages": sorted({key[0] for key in inventory}),
            "release_variants": sorted({key[1] for key in inventory}),
            "location_target": "mention spans/types, not resolved coordinates",
            "physical_rescue_incident_partition": False,
            "ordinal_dispatch_priority_label": False,
        },
        "claim_limits": [
            "IDRISI has disaster-event and location-mention supervision, not physical rescue-incident clusters.",
            "The released test files are unlabeled; no test score can be computed from this snapshot.",
            "Random and time-based releases are alternate representations/splits and must not be summed as unique tweets.",
            "The aggregate audit does not export raw text, identifiers, or person-level rows.",
            "IDRISI was not used to fit the synthetic generator.",
        ],
    }


def blocked_source_audits() -> list[dict[str, Any]]:
    """Return explicit non-evidence records for sources with unresolved access."""

    return [
        {
            "source_id": "source.trec_is",
            "audit_status": "blocked",
            "exact_urls": {
                "landing": "https://www.dcs.gla.ac.uk/~richardm/TREC_IS/",
                "data_access": (
                    "https://www.dcs.gla.ac.uk/~richardm/TREC_IS/2020/data.html"
                ),
            },
            "local_snapshot_present": False,
            "sha256": None,
            "blockers": [
                "no authorized local snapshot",
                "platform and organizer terms not accepted for this study",
                "privacy and retention review incomplete",
            ],
            "data_or_counts_imputed": False,
            "usable_as_evidence": False,
        },
        {
            "source_id": "source.crisisfacts",
            "audit_status": "blocked",
            "exact_urls": {
                "landing": "https://crisisfacts.github.io/",
                "utilities": "https://github.com/crisisfacts/utilities",
            },
            "local_snapshot_present": False,
            "sha256": None,
            "blockers": [
                "no authorized local stream snapshot",
                "mixed per-stream rights not adjudicated",
                "no pinned source manifest with byte checksums",
            ],
            "data_or_counts_imputed": False,
            "usable_as_evidence": False,
        },
    ]


def build_public_anchor(
    noaa_path: str | os.PathLike[str],
    uk_path: str | os.PathLike[str],
    idrisi_path: str | os.PathLike[str],
) -> dict[str, Any]:
    """Build the complete public anchor after all three checksum gates pass."""

    # Each audit verifies its digest before opening the payload.  Building all
    # results first prevents a partial output document when any gate fails.
    noaa = audit_noaa(noaa_path)
    uk = audit_uk_ods(uk_path)
    idrisi = audit_idrisi(idrisi_path)
    noaa_p75 = noaa["descriptive_marginals"][
        "duration_minutes_linear_quantiles"
    ]["p75"]

    return {
        "schema_version": SCHEMA_VERSION,
        "audit_id": "audit.public_external_anchor.v2",
        "audit_date": AUDIT_DATE,
        "audit_kind": "descriptive_external_sanity_audit",
        "reproduction": {
            "module": "demo.v2.public_audit",
            "subcommand": "reproduce_external",
            "checksum_policy": "fail_closed_before_parse",
            "network_access_required": False,
            "standard_library_only": True,
        },
        "audited_sources": {
            NOAA_SPEC.source_id: noaa,
            UK_SPEC.source_id: uk,
            IDRISI_SPEC.source_id: idrisi,
        },
        "blocked_sources": blocked_source_audits(),
        "anchor_mapping": {
            "status": "descriptive_only_not_generator_fitting",
            "noaa_duration_context": {
                "observed_flood_event_duration_p75_minutes": noaa_p75,
                "permitted_interpretation": (
                    "The NOAA duration distribution may inform a plausibility "
                    "check for the study's predeclared 300-minute in-distribution "
                    "time window."
                ),
                "prohibited_interpretation": (
                    "This is not a fitted rescue-report arrival window, a causal "
                    "estimate, or rescue-incident ground truth."
                ),
            },
            "uk_noaa_unit_compatibility": {
                "compatible_for_joint_parameter_estimation": False,
                "reason": (
                    "NOAA records weather-event durations; UK records attended "
                    "incidents with financial-year timing and banded/binary "
                    "responses. Their units and measurement scales are incompatible."
                ),
                "allowed_use": "separate descriptive context checks only",
            },
            "generator_fit": {
                "performed": False,
                "parameters_estimated_from_public_sources": [],
                "claim": "No audited public source was used to fit the generator.",
            },
            "unsupported_validation_targets": [
                "same-physical-incident report clustering",
                "report deduplication",
                "bounded-priority construct validity",
                "dispatch utility or harm",
                "Vietnamese-language generalization",
            ],
        },
        "seed_safety": {
            "generator_invoked": False,
            "confirmation_seeds_generated": False,
            "forbidden_confirmation_seed_interval": "4400-4439 inclusive",
            "forbidden_confirmation_seed_count": 40,
        },
        "global_claim_boundary": (
            "This artifact documents external descriptive anchors and access "
            "gaps. It does not convert public rows into study ground truth and "
            "does not strengthen causal, deployment, or real-world performance claims."
        ),
    }


def canonical_json(document: Mapping[str, Any]) -> str:
    """Serialize audit output deterministically."""

    return json.dumps(
        document,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ) + "\n"


def _write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Checksum-locked aggregate audit of external public snapshots."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    reproduce = subparsers.add_parser(
        "reproduce_external",
        help="verify and audit the three pinned snapshots without network access",
    )
    reproduce.add_argument(
        "--noaa",
        default="/tmp/nckh2-public-audit/noaa_storm_events_2024.csv.gz",
        help=f"pinned NOAA gzip CSV (SHA-256 {NOAA_SPEC.sha256})",
    )
    reproduce.add_argument(
        "--uk",
        default="/tmp/nckh2-public-audit/uk_flooding_water_rescue.ods",
        help=f"pinned UK ODS (SHA-256 {UK_SPEC.sha256})",
    )
    reproduce.add_argument(
        "--idrisi",
        default="/tmp/nckh2-public-audit/idrisi_3dfd62d.zip",
        help=f"pinned IDRISI archive (SHA-256 {IDRISI_SPEC.sha256})",
    )
    reproduce.add_argument(
        "--output",
        default="-",
        help="output JSON path, or '-' for stdout (default)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _argument_parser()
    arguments = parser.parse_args(argv)
    if arguments.command != "reproduce_external":  # pragma: no cover - argparse gate
        parser.error(f"unsupported command: {arguments.command}")
    try:
        document = build_public_anchor(
            arguments.noaa,
            arguments.uk,
            arguments.idrisi,
        )
        rendered = canonical_json(document)
        if arguments.output == "-":
            print(rendered, end="")
        else:
            _write_atomic(Path(arguments.output), rendered)
    except (PublicAuditError, OSError) as exc:
        parser.exit(2, f"public audit failed: {exc}\n")
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through CLI
    raise SystemExit(main())
