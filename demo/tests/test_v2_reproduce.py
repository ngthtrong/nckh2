from __future__ import annotations

from demo.v2 import generator
from demo.v2.reproduce import reproduce_core


def test_reproduce_core_is_exact_and_never_generates_seed(monkeypatch) -> None:
    def forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("core reproduction must not call the generator")

    monkeypatch.setattr(generator, "generate_dataset", forbidden)
    report = reproduce_core()
    assert report["status"] == "pass"
    assert report["n_master_seeds"] == 40
    assert report["analysis_exact"] is True
    assert report["short_results_exact"] is True
    assert report["oracle_diagnostic_read"] is False
    assert report["seed_generation_performed"] is False
    assert report["restricted_data_required"] is False
