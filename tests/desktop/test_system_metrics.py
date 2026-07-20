from types import SimpleNamespace

from secondbrain.desktop_native.system_metrics import (
    format_bytes,
    format_percent,
    format_uptime,
    read_system_metrics,
)


class MetricsSource:
    @staticmethod
    def virtual_memory() -> SimpleNamespace:
        return SimpleNamespace(percent=62.4)

    @staticmethod
    def swap_memory() -> SimpleNamespace:
        return SimpleNamespace(percent=4.2)

    @staticmethod
    def disk_usage(_path: str) -> SimpleNamespace:
        return SimpleNamespace(percent=25.5, total=8 * 1024**3, used=2 * 1024**3, free=6 * 1024**3)

    @staticmethod
    def boot_time() -> float:
        return 0.0

    @staticmethod
    def cpu_percent(*, interval: None) -> float:
        return 101.5


def test_metrics_are_collected_and_bounded(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("secondbrain.desktop_native.system_metrics.time.time", lambda: 90061)

    result = read_system_metrics(tmp_path, source=MetricsSource())

    assert result == {
        "available": True,
        "cpu_percent": 100.0,
        "ram_percent": 62.4,
        "swap_percent": 4.2,
        "disk_percent": 25.5,
        "disk_total": 8 * 1024**3,
        "disk_used": 2 * 1024**3,
        "disk_free": 6 * 1024**3,
        "uptime_seconds": 90061,
    }


def test_missing_or_broken_provider_degrades_safely(tmp_path) -> None:
    assert read_system_metrics(tmp_path, source=None) == {"available": False}
    assert read_system_metrics(tmp_path, source=object()) == {"available": False}


def test_metric_formatters_are_explicit() -> None:
    assert format_percent(62.4) == "62.4%"
    assert format_percent(None) == "Unavailable"
    assert format_bytes(2 * 1024**3) == "2.0 GiB"
    assert format_bytes(None) == "Unavailable"
    assert format_uptime(90061) == "1d 1h 1min"
    assert format_uptime(None) == "Unavailable"
