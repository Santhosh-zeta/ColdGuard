"""Keep opt-in performance measurements out of ordinary correctness runs."""

from pathlib import Path

import pytest


def pytest_ignore_collect(collection_path: Path, config: pytest.Config) -> bool | None:
    if collection_path == Path(__file__).parent / "perf":
        return not config.getoption("benchmark_only", default=False)
    return None
