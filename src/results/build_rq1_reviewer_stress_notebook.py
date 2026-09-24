"""Build the Colab notebook for the post-review RQ1 stress experiment.

The generated notebook is deliberately self-contained and pins the benchmark
snapshot that produced the submitted RQ1 results. Running this builder does
not execute the experiment.
"""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "RQ1_Reviewer_Stress_Colab.ipynb"


def markdown(source: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": dedent(source).strip().splitlines(keepends=True),
    }


def code(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": dedent(source).strip().splitlines(keepends=True),
    }


cells = [
    markdown(
        r"""
        # RQ1 reviewer stress test: fixed clustering configurations

        This notebook implements the post-review stress protocol for ISDS-2026
        submission 6444. It runs seven conditions on the 40 locked RQ1 test runs
        and five fixed methods: **1,400 clustering fits, with no retuning**.

        The added GPS, timestamp, and transport-copy levels are controlled
        synthetic stresses. They are not estimates of field error. Predictions
        for every method are fixed before the notebook opens ground truth.

        RQ1 ground truth labels only incident-linked reports. Accordingly,
        `ari_original`/`pair_f1_original` score the original incident-linked
        rows, while the `_all` variants score all incident-linked rows in the
        perturbed payload, including transport copies. Fake-report behavior is
        evaluated separately over the full payload using absorption, rejection,
        contamination, and false-destination diagnostics.

        Workflow: run setup and integrity gates, run the 35-fit smoke test, run
        the full resumable batch, aggregate, then package and download the ZIP.
        Keep the executed notebook with the ZIP.
        """
    ),
    markdown(
        r"""
        ## Setup and provenance gates

        The next three steps check out the immutable benchmark snapshot, install
        the exact versions recorded by its original notebook, and verify the
        source notebook, selected configuration, and 40-run test data before any
        clustering is allowed to start.
        """
    ),
    code(
        r"""
        #@title 1. Checkout the exact benchmark snapshot and install its pinned environment
        from pathlib import Path
        import importlib.metadata as package_metadata
        import os, subprocess, sys

        REPOSITORY_URL = "https://github.com/ngthtrong/nckh2.git"
        SOURCE_COMMIT = "6ac75c202d04934deb46d84486132e54d42d735f"
        REPO = Path("/content/nckh2-rq1-source")

        if not (REPO / ".git").exists():
            REPO.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "init", str(REPO)], check=True)
            subprocess.run(["git", "-C", str(REPO), "remote", "add", "origin", REPOSITORY_URL], check=True)
        subprocess.run(["git", "-C", str(REPO), "fetch", "--depth", "1", "origin", SOURCE_COMMIT], check=True)
        subprocess.run(["git", "-C", str(REPO), "checkout", "--detach", "FETCH_HEAD"], check=True)
        actual_commit = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip()
        assert actual_commit == SOURCE_COMMIT, (actual_commit, SOURCE_COMMIT)

        SUPPORTED_PYTHON_MIN = (3, 11)
        SUPPORTED_PYTHON_MAX = (3, 13)
        python_major_minor = sys.version_info[:2]
        assert SUPPORTED_PYTHON_MIN <= python_major_minor <= SUPPORTED_PYTHON_MAX, (
            f"Python {sys.version.split()[0]} is unsupported; use Python 3.11-3.13 "
            "(Python 3.12 is recommended for exact source-environment reproduction)."
        )
        if python_major_minor != (3, 12):
            print(
                f"NOTICE: running on Python {sys.version.split()[0]}; the source benchmark "
                "used Python 3.12. The exact runtime will be recorded in the protocol and manifest."
            )
        REQUIRED = {
            "numpy": "2.5.1", "pandas": "3.0.3", "matplotlib": "3.11.0",
            "networkx": "3.6.1", "python-louvain": "0.16",
            "scikit-learn": "1.9.0", "scipy": "1.18.0",
            "igraph": "1.0.0", "leidenalg": "0.12.0",
        }
        installed = {}
        for name in REQUIRED:
            try:
                installed[name] = package_metadata.version(name)
            except package_metadata.PackageNotFoundError:
                installed[name] = None
        if installed != REQUIRED:
            specs = [f"{name}=={version}" for name, version in REQUIRED.items()]
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-q", "--upgrade",
                 "--upgrade-strategy", "only-if-needed", *specs],
                check=True,
            )
            print("Pinned packages installed; the Colab runtime will restart once. Run all again after reconnecting.")
            os.kill(os.getpid(), 9)
        assert {name: package_metadata.version(name) for name in REQUIRED} == REQUIRED
        subprocess.run(
            [sys.executable, "-c", "import numpy,scipy,sklearn,community,igraph,leidenalg"],
            check=True,
        )
        print("PASS source commit and pinned environment:", actual_commit, REQUIRED)
        """
    ),
    code(
        r"""
        #@title 2. Locked protocol and durable output location
        import csv, hashlib, importlib.metadata, json, math, os, platform, shutil, time, zipfile
        from datetime import datetime, timezone
        from pathlib import Path

        import igraph as ig
        import leidenalg
        import networkx as nx
        import numpy as np
        import pandas as pd
        from community import community_louvain
        from scipy.stats import wilcoxon
        from sklearn.cluster import DBSCAN
        from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

        USE_GOOGLE_DRIVE = True
        RUN_FULL = True  # Set False only when you intentionally want a smoke-only run.

        if USE_GOOGLE_DRIVE:
            from google.colab import drive
            drive.mount("/content/drive")
            ARTIFACT_ROOT = Path("/content/drive/MyDrive/nckh2-rq1-reviewer-stress")
        else:
            ARTIFACT_ROOT = Path("/content/nckh2-rq1-reviewer-stress")

        DATA_ROOT = REPO / "src" / "data"
        SOURCE_NOTEBOOK_PATH = REPO / "src" / "results" / "Benchmark_Cij_Baselines_Colab.ipynb"
        SELECTED_CONFIG_PATH = REPO / "src" / "results" / "cij_baseline_benchmark_results" / "selected_configs.json"
        TEST_RUN_IDS = tuple(f"run_{seed:03d}" for seed in range(41, 81))
        METHODS = (
            "product_cij_louvain",
            "additive_cij_louvain",
            "additive_cij_louvain_matched_density",
            "product_cij_leiden",
            "geo_time_dbscan",
        )
        SCENARIOS = {
            "baseline": {"kind": "baseline"},
            "gps_noise_100m": {"kind": "gps", "sigma_m": 100.0},
            "gps_noise_300m": {"kind": "gps", "sigma_m": 300.0},
            "time_noise_15min": {"kind": "time", "sigma_min": 15.0},
            "time_noise_60min": {"kind": "time", "sigma_min": 60.0},
            "exact_transport_copy_2x": {"kind": "duplicate", "copies": 2},
            "exact_transport_copy_5x": {"kind": "duplicate", "copies": 5},
        }
        EXPECTED_DATA_TREE = "5bb8f9e5f1bb1c4deec8f0db1351e27d1bf30333"
        EXPECTED_SOURCE_NOTEBOOK_SHA256 = "13a586af7ac5331dd1afe354b9e5c9a46b90e0ff2f6ac6f71dbdc3badd6ca7ef"
        EXPECTED_SELECTED_CONFIG_SHA256 = "e3c9f1ad333575862126315595835f01a7b660ac59c240ed0e282f653fb265f6"
        STRESS_IMPLEMENTATION_ID = "rq1-reviewer-stress-2026-09-08-v1"
        STRESS_RANDOM_SEED = 20260908
        BOOTSTRAP_RANDOM_SEED = 20260729
        BOOTSTRAP_RESAMPLES = 5000
        EXPECTED_FITS = len(TEST_RUN_IDS) * len(SCENARIOS) * len(METHODS)
        assert EXPECTED_FITS == 1400

        FULL_ROOT = ARTIFACT_ROOT / "full"
        SMOKE_ROOT = ARTIFACT_ROOT / "smoke"
        FULL_ROOT.mkdir(parents=True, exist_ok=True)
        SMOKE_ROOT.mkdir(parents=True, exist_ok=True)
        print("Artifact root:", ARTIFACT_ROOT)
        print("Locked fits:", EXPECTED_FITS)
        """
    ),
    code(
        r"""
        #@title 3. Integrity and provenance gate
        def sha256_file(path):
            h = hashlib.sha256()
            with open(path, "rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    h.update(chunk)
            return h.hexdigest()

        def canonical_sha256(value):
            payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
            return hashlib.sha256(payload).hexdigest()

        actual_data_tree = subprocess.check_output(
            ["git", "-C", str(REPO), "rev-parse", "HEAD:src/data"], text=True
        ).strip()
        assert actual_data_tree == EXPECTED_DATA_TREE, (actual_data_tree, EXPECTED_DATA_TREE)
        assert sha256_file(SOURCE_NOTEBOOK_PATH) == EXPECTED_SOURCE_NOTEBOOK_SHA256
        assert sha256_file(SELECTED_CONFIG_PATH) == EXPECTED_SELECTED_CONFIG_SHA256

        run_dirs = [DATA_ROOT / "gold" / run_id for run_id in TEST_RUN_IDS]
        assert all(path.is_dir() for path in run_dirs)
        required_names = ("algorithm_input.json", "ground_truth.json", "run_manifest.json")
        inventory = []
        for run_dir in run_dirs:
            for name in required_names:
                path = run_dir / name
                assert path.is_file(), path
                inventory.append({"path": str(path.relative_to(REPO)), "sha256": sha256_file(path)})
        dataset_inventory_sha256 = canonical_sha256(inventory)

        selected_payload = json.loads(SELECTED_CONFIG_PATH.read_text())
        SELECTED = selected_payload["selected"]
        assert set(METHODS) <= set(SELECTED)

        PROTOCOL = {
            "protocol_id": "ISDS-6444-RQ1-reviewer-stress-v1",
            "implementation_id": STRESS_IMPLEMENTATION_ID,
            "source_commit": SOURCE_COMMIT,
            "python_version": platform.python_version(),
            "source_notebook_sha256": EXPECTED_SOURCE_NOTEBOOK_SHA256,
            "data_tree": EXPECTED_DATA_TREE,
            "dataset_inventory_sha256": dataset_inventory_sha256,
            "selected_config_sha256": EXPECTED_SELECTED_CONFIG_SHA256,
            "selected_configs": {method: SELECTED[method] for method in METHODS},
            "test_runs": list(TEST_RUN_IDS),
            "methods": list(METHODS),
            "scenarios": SCENARIOS,
            "stress_random_seed": STRESS_RANDOM_SEED,
            "bootstrap_random_seed": BOOTSTRAP_RANDOM_SEED,
            "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
            "no_retuning": True,
            "prediction_before_truth": True,
            "interpretation": "Synthetic stress levels; not estimates of field error.",
        }
        PROTOCOL_SHA256 = canonical_sha256(PROTOCOL)
        print("PASS data tree:", actual_data_tree)
        print("PASS source notebook SHA-256:", EXPECTED_SOURCE_NOTEBOOK_SHA256)
        print("PASS selected configuration SHA-256:", EXPECTED_SELECTED_CONFIG_SHA256)
        print("Dataset inventory SHA-256:", dataset_inventory_sha256)
        print("Protocol SHA-256:", PROTOCOL_SHA256)
        """
    ),
    markdown(
        r"""
        ## Controlled perturbations and fixed methods

        These steps implement the seven one-factor-at-a-time conditions and the
        five already selected clustering methods. The duplicate lineage is
        evaluator-only, and the transformation checks do not run clustering.
        """
    ),
    code(
        r"""
        #@title 4. Data loading and deterministic stress transformations
        EARTH_RADIUS_M = 6_371_000.0

        def read_json(path):
            return json.loads(Path(path).read_text(encoding="utf-8"))

        def load_input(run_dir):
            payload = read_json(run_dir / "algorithm_input.json")
            rows = payload["reports"]
            lat = np.radians(np.array([float(row["lat"]) for row in rows]))
            lng = np.radians(np.array([float(row["lng"]) for row in rows]))
            minute = np.array([
                datetime.fromisoformat(row["created_at"]).timestamp() / 60.0 for row in rows
            ])
            minute -= minute.min()
            x = {
                "dataset_id": payload["dataset_id"],
                "seed": int(payload["seed"]),
                "event_id": [str(row["event_id"]) for row in rows],
                "lat_rad": lat,
                "lng_rad": lng,
                "minute": minute,
                "flood": np.array([float(row["flood"]) for row in rows]),
                "urgency": np.array([float(row["urgency"]) for row in rows]),
                "obs_f": np.array(["flood" not in row.get("missing_fields", []) for row in rows]),
                "obs_e": np.array(["urgency" not in row.get("missing_fields", []) for row in rows]),
            }
            return with_local_coordinates(x)

        def with_local_coordinates(x):
            lat0, lng0 = np.median(x["lat_rad"]), np.median(x["lng_rad"])
            x["east"] = EARTH_RADIUS_M * np.cos(lat0) * (x["lng_rad"] - lng0)
            x["north"] = EARTH_RADIUS_M * (x["lat_rad"] - lat0)
            return x

        def load_truth(run_dir, event_ids):
            payload = read_json(run_dir / "ground_truth.json")
            by_id = {str(row["event_id"]): int(row["gt_cluster"]) for row in payload["report_labels"]}
            assert set(by_id) == set(event_ids)
            return np.array([by_id[event_id] for event_id in event_ids], dtype=int)

        def copy_x(x):
            out = {}
            for key, value in x.items():
                if isinstance(value, np.ndarray):
                    out[key] = value.copy()
                elif isinstance(value, list):
                    out[key] = list(value)
                else:
                    out[key] = value
            return out

        def deterministic_rng(run_seed, scenario_name):
            token = f"{STRESS_RANDOM_SEED}|{run_seed}|{scenario_name}".encode()
            seed = int.from_bytes(hashlib.sha256(token).digest()[:8], "big")
            return np.random.default_rng(seed)

        def transform_input(base, scenario_name):
            spec = SCENARIOS[scenario_name]
            x = copy_x(base)
            n = len(base["event_id"])
            source_indices = np.arange(n, dtype=int)
            mapping = []
            if spec["kind"] == "baseline":
                return x, source_indices, mapping
            if spec["kind"] == "gps":
                rng = deterministic_rng(base["seed"], scenario_name)
                east_noise = rng.normal(0.0, spec["sigma_m"], size=n)
                north_noise = rng.normal(0.0, spec["sigma_m"], size=n)
                x["lat_rad"] += north_noise / EARTH_RADIUS_M
                cos_lat = np.maximum(np.cos(x["lat_rad"]), 1e-12)
                x["lng_rad"] += east_noise / (EARTH_RADIUS_M * cos_lat)
                return with_local_coordinates(x), source_indices, mapping
            if spec["kind"] == "time":
                rng = deterministic_rng(base["seed"], scenario_name)
                x["minute"] += rng.normal(0.0, spec["sigma_min"], size=n)
                return x, source_indices, mapping
            if spec["kind"] == "duplicate":
                copies = int(spec["copies"])
                source_indices = np.tile(np.arange(n, dtype=int), copies)
                for key, value in list(x.items()):
                    if isinstance(value, np.ndarray) and len(value) == n:
                        x[key] = value[source_indices]
                event_ids = []
                for copy_index in range(copies):
                    for event_id in base["event_id"]:
                        clone_id = event_id if copy_index == 0 else f"{event_id}__transport_copy_{copy_index + 1}"
                        event_ids.append(clone_id)
                        mapping.append({
                            "run_id": base["dataset_id"],
                            "scenario": scenario_name,
                            "source_event_id": event_id,
                            "perturbed_event_id": clone_id,
                            "copy_index": copy_index,
                            "evaluator_only": True,
                        })
                x["event_id"] = event_ids
                return with_local_coordinates(x), source_indices, mapping
            raise ValueError(spec)

        # Transformation invariants; no clustering is run in this cell.
        toy = load_input(DATA_ROOT / "gold" / TEST_RUN_IDS[0])
        for name, spec in SCENARIOS.items():
            transformed, source_indices, mapping = transform_input(toy, name)
            expected_size = len(toy["event_id"]) * int(spec.get("copies", 1))
            assert len(transformed["event_id"]) == expected_size
            assert len(source_indices) == expected_size
            if spec["kind"] == "duplicate":
                assert np.array_equal(transformed["flood"], toy["flood"][source_indices])
                assert np.array_equal(transformed["minute"], toy["minute"][source_indices])
                assert len(mapping) == expected_size
        print("PASS all seven deterministic transformation contracts")
        """
    ),
    markdown(
        r"""
        ## Smoke check and resumable full run

        The 35-fit smoke check runs first and must pass before the full batch can
        start. The full batch checkpoints every run-condition so it can resume
        from Google Drive without dropping adverse outcomes. Set `RUN_FULL =
        False` in step 2 only when you intentionally want a smoke-only run; in
        that mode, stop after step 6.
        """
    ),
    code(
        r"""
        #@title 5. Fixed graph builders, clusterers, and metrics
        TAU_F, TAU_E = 0.25, 0.35
        BETA, GAMMA = 0.5, 0.5

        def pair_matrices(x):
            lat, lng = x["lat_rad"], x["lng_rad"]
            dlat = lat[:, None] - lat[None, :]
            dlng = lng[:, None] - lng[None, :]
            hav = np.sin(dlat / 2) ** 2 + np.cos(lat)[:, None] * np.cos(lat)[None, :] * np.sin(dlng / 2) ** 2
            distance = 2 * EARTH_RADIUS_M * np.arcsin(np.sqrt(np.clip(hav, 0, 1)))
            dt = np.abs(x["minute"][:, None] - x["minute"][None, :])
            i_f = (x["obs_f"][:, None] & x["obs_f"][None, :]).astype(float)
            i_e = (x["obs_e"][:, None] & x["obs_e"][None, :]).astype(float)
            observed = i_f + i_e
            context = (observed / 2) * np.exp(
                -i_f * np.abs(x["flood"][:, None] - x["flood"][None, :]) / TAU_F
                -i_e * np.abs(x["urgency"][:, None] - x["urgency"][None, :]) / TAU_E
            )
            context[observed == 0] = 0
            np.fill_diagonal(context, 0)
            return distance, dt, context

        def threshold_knn(weights, quantile, knn):
            out = weights.copy()
            np.fill_diagonal(out, 0)
            values = out[np.triu_indices(len(out), 1)]
            values = values[values > 0]
            theta = float(np.quantile(values, quantile)) if len(values) else math.inf
            out[out <= theta] = 0
            if 0 < knn < len(out):
                mask = np.zeros_like(out, dtype=bool)
                for index, row in enumerate(out):
                    candidates = np.nonzero(row)[0]
                    top = np.argpartition(row, -knn)[-knn:] if len(candidates) > knn else candidates
                    mask[index, top] = True
                out = np.where(mask | mask.T, out, 0)
            np.fill_diagonal(out, 0)
            return out, theta

        def louvain(weights):
            graph = nx.Graph()
            graph.add_nodes_from(range(len(weights)))
            left, right = np.nonzero(np.triu(weights, 1))
            graph.add_weighted_edges_from(
                (int(i), int(j), float(weights[i, j])) for i, j in zip(left, right)
            )
            if not graph.number_of_edges():
                return np.arange(len(weights))
            partition = community_louvain.best_partition(
                graph, weight="weight", resolution=1.2, random_state=42
            )
            return np.array([partition.get(i, i) for i in range(len(weights))])

        def leiden(weights, resolution):
            left, right = np.nonzero(np.triu(weights, 1))
            edges = list(zip(left.tolist(), right.tolist()))
            if not edges:
                return np.arange(len(weights))
            graph = ig.Graph(n=len(weights), edges=edges)
            graph.es["weight"] = [float(weights[i, j]) for i, j in edges]
            partition = leidenalg.find_partition(
                graph,
                leidenalg.RBConfigurationVertexPartition,
                weights="weight",
                resolution_parameter=resolution,
                seed=42,
            )
            labels = np.zeros(len(weights), dtype=int)
            for cluster_id, members in enumerate(partition):
                labels[list(members)] = cluster_id
            return labels

        def graph_for(method, pairs):
            distance, dt, context = pairs
            if method == "product_cij_leiden":
                config = SELECTED["product_cij_louvain"]
            else:
                config = SELECTED[method]
            geo = np.exp(-(distance ** 2) / (2 * config.get("sigma", 700) ** 2))
            temporal = np.exp(-dt / config.get("tau_t", 60))
            if method in {"product_cij_louvain", "product_cij_leiden"}:
                dense = geo * (BETA * temporal + GAMMA * context)
            elif method in {"additive_cij_louvain", "additive_cij_louvain_matched_density"}:
                dense = config["alpha"] * geo + BETA * temporal + GAMMA * context
            else:
                raise ValueError(method)
            return threshold_knn(dense, config["q"], config["knn"])

        def predict(method, x, pairs):
            if method in {
                "product_cij_louvain",
                "additive_cij_louvain",
                "additive_cij_louvain_matched_density",
            }:
                graph, threshold = graph_for(method, pairs)
                return louvain(graph), graph, threshold
            if method == "product_cij_leiden":
                graph, threshold = graph_for(method, pairs)
                return leiden(graph, SELECTED[method]["resolution"]), graph, threshold
            if method == "geo_time_dbscan":
                distance, dt, _ = pairs
                config = SELECTED[method]
                dissimilarity = np.maximum(
                    distance / config["spatial_eps"], dt / config["temporal_eps"]
                )
                np.fill_diagonal(dissimilarity, 0)
                labels = DBSCAN(
                    eps=1.0, min_samples=config["min_samples"], metric="precomputed"
                ).fit_predict(dissimilarity)
                return labels, None, 1.0
            raise ValueError(method)

        def pairwise_f1(labels, truth, noise_label=None):
            keep = truth >= 0
            labels, truth = np.asarray(labels)[keep], truth[keep]
            upper = np.triu_indices(len(truth), 1)
            actual = (truth[:, None] == truth[None, :])[upper]
            same = labels[:, None] == labels[None, :]
            if noise_label is not None:
                rejected = labels == noise_label
                same &= ~(rejected[:, None] | rejected[None, :])
            predicted = same[upper]
            tp = np.sum(actual & predicted)
            fp = np.sum(~actual & predicted)
            fn = np.sum(actual & ~predicted)
            precision = tp / (tp + fp) if tp + fp else 0
            recall = tp / (tp + fn) if tp + fn else 0
            return float(2 * precision * recall / (precision + recall)) if precision + recall else 0.0

        def evaluate(labels, truth, noise_label):
            labels = np.asarray(labels)
            keep = truth >= 0
            unassigned = labels == noise_label if noise_label is not None else np.zeros(len(labels), dtype=bool)
            groups = {}
            for index, label in enumerate(labels):
                if not unassigned[index]:
                    groups.setdefault(int(label), []).append(index)
            labeled_groups = [idx for idx in groups.values() if np.any(truth[idx] >= 0)]
            fake_only_groups = [idx for idx in groups.values() if np.all(truth[idx] < 0)]
            mixed_groups = [idx for idx in groups.values() if np.any(truth[idx] >= 0) and np.any(truth[idx] < 0)]
            n_fake, n_genuine = int(np.sum(truth < 0)), int(np.sum(truth >= 0))
            fake_absorbed = sum(np.sum(truth[idx] < 0) for idx in labeled_groups)
            fake_rejected = int(np.sum((truth < 0) & unassigned))
            genuine_rejected = int(np.sum((truth >= 0) & unassigned))
            return {
                "ari": float(adjusted_rand_score(truth[keep], labels[keep])),
                "nmi": float(normalized_mutual_info_score(truth[keep], labels[keep])),
                "pair_f1": pairwise_f1(labels, truth, noise_label),
                "fake_absorption_rate": 100 * fake_absorbed / n_fake if n_fake else 0.0,
                "fake_rejection_rate": 100 * fake_rejected / n_fake if n_fake else 0.0,
                "genuine_rejection_rate": 100 * genuine_rejected / n_genuine if n_genuine else 0.0,
                "false_destination_rate": 100 * len(fake_only_groups) / len(groups) if groups else 0.0,
                "fake_only_destinations": len(fake_only_groups),
                "contaminated_destinations": len(mixed_groups),
                "n_clusters": len(groups),
                "n_unassigned": int(unassigned.sum()),
            }

        def graph_stats(graph):
            if graph is None:
                return {"n_edges": np.nan, "retained_edge_fraction": np.nan, "mean_degree": np.nan}
            n = len(graph)
            n_edges = int(np.count_nonzero(np.triu(graph, 1)))
            total = n * (n - 1) / 2
            return {
                "n_edges": n_edges,
                "retained_edge_fraction": float(n_edges / total) if total else 0.0,
                "mean_degree": float(2 * n_edges / n) if n else 0.0,
            }

        # Verify the three missingness branches used by the paper formula.
        toy = {
            "lat_rad": np.zeros(4), "lng_rad": np.zeros(4), "minute": np.zeros(4),
            "flood": np.array([.2, .5, .5, .5]), "urgency": np.array([.8, .1, .1, .1]),
            "obs_f": np.array([True, True, True, False]),
            "obs_e": np.array([True, True, False, False]),
        }
        _, _, toy_context = pair_matrices(toy)
        assert np.isclose(toy_context[0, 1], math.exp(-.3 / TAU_F - .7 / TAU_E))
        assert np.isclose(toy_context[0, 2], .5 * math.exp(-.3 / TAU_F))
        assert toy_context[0, 3] == 0.0
        print("PASS formula branches and fixed prediction functions")
        """
    ),
    code(
        r"""
        #@title 6. Atomic checkpoints and one-run smoke test (35 fits)
        def atomic_write_json(path, value):
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(path.suffix + ".tmp")
            temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
            os.replace(temporary, path)

        def finite_or_none(value):
            value = float(value)
            return value if np.isfinite(value) else None

        def run_checkpoint(run_id, scenario_name, output_root, resume=True):
            checkpoint = output_root / "checkpoints" / f"{run_id}__{scenario_name}.json"
            if resume and checkpoint.exists():
                cached = read_json(checkpoint)
                assert cached["protocol_sha256"] == PROTOCOL_SHA256
                assert cached["source_commit"] == SOURCE_COMMIT
                return cached

            run_dir = DATA_ROOT / "gold" / run_id
            base = load_input(run_dir)
            transformed, source_indices, mapping = transform_input(base, scenario_name)
            pairs = pair_matrices(transformed)

            # Lock every prediction before reading evaluator-only truth.
            predictions, runtimes = {}, {}
            for method in METHODS:
                started = time.perf_counter()
                labels, graph, threshold = predict(method, transformed, pairs)
                predictions[method] = {"labels": labels, "graph": graph, "threshold": threshold}
                runtimes[method] = time.perf_counter() - started

            base_truth = load_truth(run_dir, base["event_id"])
            truth = base_truth[source_indices]
            original_indices = np.arange(len(base_truth), dtype=int)
            rows = []
            for method, prediction in predictions.items():
                noise_label = -1 if method == "geo_time_dbscan" else None
                original = evaluate(prediction["labels"][original_indices], base_truth, noise_label)
                full = evaluate(prediction["labels"], truth, noise_label)
                graph_metrics = graph_stats(prediction["graph"])
                row = {
                    "run_id": run_id,
                    "seed": int(base["seed"]),
                    "scenario": scenario_name,
                    "method": method,
                    "n_original_reports": len(base_truth),
                    "n_evaluated_reports": len(truth),
                    "runtime_seconds": runtimes[method],
                    "threshold": prediction["threshold"],
                    **graph_metrics,
                }
                row.update({f"{key}_original": value for key, value in original.items()})
                row.update({f"{key}_all": value for key, value in full.items()})
                rows.append({key: finite_or_none(value) if isinstance(value, (float, np.floating)) else value for key, value in row.items()})

            payload = {
                "protocol_sha256": PROTOCOL_SHA256,
                "source_commit": SOURCE_COMMIT,
                "data_tree": EXPECTED_DATA_TREE,
                "run_id": run_id,
                "scenario": scenario_name,
                "rows": rows,
                "duplication_mapping": mapping,
            }
            atomic_write_json(checkpoint, payload)
            return payload

        smoke_started = time.perf_counter()
        smoke_payloads = [
            run_checkpoint(TEST_RUN_IDS[0], scenario, SMOKE_ROOT, resume=False)
            for scenario in SCENARIOS
        ]
        smoke_seconds = time.perf_counter() - smoke_started
        smoke_rows = [row for payload in smoke_payloads for row in payload["rows"]]
        assert len(smoke_rows) == len(SCENARIOS) * len(METHODS) == 35
        assert all(row["ari_original"] is not None for row in smoke_rows)
        print(f"PASS smoke: 35 fits in {smoke_seconds:.1f} s")
        print(f"Measured serial estimate for 1,400 fits: {smoke_seconds * len(TEST_RUN_IDS) / 60:.1f} min")
        display(pd.DataFrame(smoke_rows)[["scenario", "method", "ari_original", "pair_f1_original", "runtime_seconds"]])
        """
    ),
    code(
        r"""
        #@title 7. Full resumable batch
        assert RUN_FULL, "Smoke-only mode is active; stop after cell 6 or set RUN_FULL = True in cell 2."
        failures_path = FULL_ROOT / "failures.jsonl"
        completed = 0
        full_started = time.perf_counter()
        for run_id in TEST_RUN_IDS:
            for scenario_name in SCENARIOS:
                try:
                    run_checkpoint(run_id, scenario_name, FULL_ROOT, resume=True)
                    completed += len(METHODS)
                except Exception as error:
                    with open(failures_path, "a", encoding="utf-8") as handle:
                        handle.write(json.dumps({
                            "run_id": run_id,
                            "scenario": scenario_name,
                            "error_type": type(error).__name__,
                            "error": str(error),
                            "protocol_sha256": PROTOCOL_SHA256,
                        }, sort_keys=True) + "\n")
                    raise
            print(f"{run_id}: {completed}/{EXPECTED_FITS} fits checkpointed")
        elapsed = time.perf_counter() - full_started
        assert completed == EXPECTED_FITS
        print(f"PASS full batch: {completed} fits; current-session elapsed {elapsed / 60:.1f} min")
        """
    ),
    code(
        r"""
        #@title 8. Aggregate paired effects and validate completeness
        checkpoints = sorted((FULL_ROOT / "checkpoints").glob("run_*__*.json"))
        assert len(checkpoints) == len(TEST_RUN_IDS) * len(SCENARIOS) == 280
        if failures_path.exists() and failures_path.read_text(encoding="utf-8").strip():
            raise RuntimeError("failures.jsonl is non-empty; resolve every failure before aggregation")
        payloads = [read_json(path) for path in checkpoints]
        assert all(payload["protocol_sha256"] == PROTOCOL_SHA256 for payload in payloads)
        rows = [row for payload in payloads for row in payload["rows"]]
        mappings = [row for payload in payloads for row in payload["duplication_mapping"]]
        frame = pd.DataFrame(rows)
        assert len(frame) == EXPECTED_FITS
        assert frame.groupby(["run_id", "scenario", "method"]).size().eq(1).all()

        aggregate_dir = FULL_ROOT / "aggregate"
        aggregate_dir.mkdir(parents=True, exist_ok=True)
        per_run_path = aggregate_dir / "rq1_stress_per_run.csv"
        mapping_path = aggregate_dir / "rq1_stress_duplication_mapping.csv"
        summary_path = aggregate_dir / "rq1_stress_summary.csv"
        effects_path = aggregate_dir / "rq1_stress_paired_effects.csv"
        runtime_path = aggregate_dir / "rq1_stress_runtime_log.csv"
        frame.to_csv(per_run_path, index=False)
        pd.DataFrame(mappings).to_csv(mapping_path, index=False)

        metric_columns = [
            "ari_original", "pair_f1_original", "ari_all", "pair_f1_all",
            "fake_absorption_rate_all", "fake_rejection_rate_all",
            "genuine_rejection_rate_all", "false_destination_rate_all",
            "retained_edge_fraction", "mean_degree",
        ]
        summary = frame.groupby(["scenario", "method"], as_index=False)[metric_columns].agg(["mean", "std", "count"])
        summary.columns = ["_".join(part for part in column if part) for column in summary.columns.to_flat_index()]
        summary.to_csv(summary_path, index=False)
        frame[["run_id", "seed", "scenario", "method", "runtime_seconds"]].to_csv(runtime_path, index=False)

        def paired_bootstrap(values, seed):
            values = np.asarray(values, dtype=float)
            values = values[np.isfinite(values)]
            if not len(values):
                return None, None, None, 0
            rng = np.random.default_rng(seed)
            means = np.mean(rng.choice(values, size=(BOOTSTRAP_RESAMPLES, len(values)), replace=True), axis=1)
            return float(np.mean(values)), float(np.quantile(means, .025)), float(np.quantile(means, .975)), len(values)

        direction = {
            "ari_original": "higher", "pair_f1_original": "higher",
            "ari_all": "higher", "pair_f1_all": "higher",
            "fake_absorption_rate_all": "lower", "fake_rejection_rate_all": "descriptive",
            "genuine_rejection_rate_all": "lower", "false_destination_rate_all": "lower",
            "retained_edge_fraction": "descriptive", "mean_degree": "descriptive",
        }
        effects = []
        for method in METHODS:
            baseline = frame[(frame.method == method) & (frame.scenario == "baseline")].set_index("run_id")
            for scenario_name in SCENARIOS:
                if scenario_name == "baseline":
                    continue
                stressed = frame[(frame.method == method) & (frame.scenario == scenario_name)].set_index("run_id")
                common = sorted(set(baseline.index) & set(stressed.index))
                assert len(common) == len(TEST_RUN_IDS)
                for metric in metric_columns:
                    differences = stressed.loc[common, metric].astype(float).to_numpy() - baseline.loc[common, metric].astype(float).to_numpy()
                    seed_token = hashlib.sha256(f"{BOOTSTRAP_RANDOM_SEED}|{method}|{scenario_name}|{metric}".encode()).digest()
                    mean_delta, low, high, n = paired_bootstrap(differences, int.from_bytes(seed_token[:8], "big"))
                    effects.append({
                        "method": method, "scenario": scenario_name, "metric": metric,
                        "direction": direction[metric], "mean_stress_minus_baseline": mean_delta,
                        "bootstrap_ci95_low": low, "bootstrap_ci95_high": high,
                        "paired_runs": n, "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
                    })
        effects_frame = pd.DataFrame(effects)
        effects_frame.to_csv(effects_path, index=False)
        assert effects_frame.paired_runs.dropna().isin([0, 40]).all()
        print("PASS aggregation:", len(frame), "fit rows,", len(effects_frame), "paired effect rows")
        display(summary.head(15))
        display(effects_frame[effects_frame.metric.isin(["ari_original", "pair_f1_original"])])
        """
    ),
    markdown(
        r"""
        ## Results and handoff

        The final step captures the executed notebook where Colab permits it,
        writes a checksum manifest, and creates a timestamped ZIP. Send both the
        ZIP and the executed notebook back for independent acceptance checks.
        """
    ),
    code(
        r"""
        #@title 9. Capture the executed notebook, manifest, ZIP, and download
        executed_notebook_path = FULL_ROOT / "RQ1_Reviewer_Stress_Colab.executed.ipynb"
        notebook_capture = {"status": "unavailable"}
        try:
            from google.colab import _message
            response = _message.blocking_request("get_ipynb", timeout_sec=600)
            notebook_payload = response.get("ipynb", response)
            assert isinstance(notebook_payload, dict) and "cells" in notebook_payload
            executed_notebook_path.write_text(json.dumps(notebook_payload, ensure_ascii=False, indent=1))
            notebook_capture = {"status": "captured", "path": executed_notebook_path.name}
        except Exception as error:
            notebook_capture = {"status": "manual-download-required", "error": str(error)}
            print("Use File > Download > Download .ipynb and keep it beside the ZIP.")

        package_versions = {
            name: importlib.metadata.version(name)
            for name in ("numpy", "pandas", "scipy", "scikit-learn", "networkx", "python-louvain", "igraph", "leidenalg")
        }
        atomic_write_json(FULL_ROOT / "protocol.json", PROTOCOL)
        atomic_write_json(
            FULL_ROOT / "selected_configs.used.json",
            {"sha256": EXPECTED_SELECTED_CONFIG_SHA256,
             "selected": {method: SELECTED[method] for method in METHODS}},
        )
        artifact_files = sorted(
            path for path in FULL_ROOT.rglob("*")
            if path.is_file() and path.name != "manifest.json"
        )
        created_at = datetime.now(timezone.utc)
        manifest = {
            "protocol": PROTOCOL,
            "protocol_sha256": PROTOCOL_SHA256,
            "created_at_utc": created_at.isoformat(),
            "fit_rows": EXPECTED_FITS,
            "checkpoint_count": len(list((FULL_ROOT / "checkpoints").glob("*.json"))),
            "package_versions": package_versions,
            "python_version": sys.version,
            "executed_notebook": notebook_capture,
            "artifacts": {
                str(path.relative_to(FULL_ROOT)): sha256_file(path) for path in artifact_files
            },
            "limitations": [
                "All added perturbations are synthetic stress levels, not estimates of field error.",
                "No configuration was retuned on the test runs.",
                "Ground truth was loaded only after all five predictions for each run-condition were fixed.",
            ],
        }
        atomic_write_json(FULL_ROOT / "manifest.json", manifest)

        run_stamp = created_at.strftime("%Y%m%dT%H%M%SZ")
        zip_path = ARTIFACT_ROOT.parent / f"nckh2-rq1-reviewer-stress-{run_stamp}.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(FULL_ROOT.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(FULL_ROOT.parent))
        print("ZIP:", zip_path)
        print("ZIP SHA-256:", sha256_file(zip_path))
        print("Executed notebook:", notebook_capture)

        from google.colab import files
        files.download(str(zip_path))
        """
    ),
]


notebook = {
    "cells": cells,
    "metadata": {
        "accelerator": "CPU",
        "colab": {"name": OUTPUT.name, "provenance": []},
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

OUTPUT.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(OUTPUT)
