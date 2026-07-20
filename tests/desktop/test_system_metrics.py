from types import SimpleNamespace

from secondbrain.desktop_native.system_metrics import (
    SystemMetricsSampler,
    format_bytes,
    format_kbps,
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
    assert format_kbps(12.34) == "12.3 KB/s"
    assert format_kbps(None) == "Unavailable"


def test_network_sampler_calculates_rates_between_snapshots(tmp_path) -> None:
    source = MetricsSource()
    counters = iter(
        [
            SimpleNamespace(bytes_sent=1024, bytes_recv=2048),
            SimpleNamespace(bytes_sent=3072, bytes_recv=6144),
        ]
    )
    source.net_io_counters = lambda: next(counters)
    ticks = iter([10.0, 12.0])
    sampler = SystemMetricsSampler(source=source, clock=lambda: next(ticks))

    first = sampler.read(tmp_path)
    second = sampler.read(tmp_path)

    assert first["net_up_kbps"] == 0.0
    assert first["net_down_kbps"] == 0.0
    assert second["net_up_kbps"] == 1.0
    assert second["net_down_kbps"] == 2.0


def test_network_sampler_handles_counter_reset_and_failure(tmp_path) -> None:
    source = MetricsSource()
    source.net_io_counters = lambda: SimpleNamespace(bytes_sent=1, bytes_recv=1)
    ticks = iter([10.0, 11.0])
    sampler = SystemMetricsSampler(source=source, clock=lambda: next(ticks))
    sampler.read(tmp_path)
    result = sampler.read(tmp_path)
    assert result["net_up_kbps"] == 0.0
    assert result["net_down_kbps"] == 0.0

    source.net_io_counters = lambda: (_ for _ in ()).throw(OSError("unavailable"))
    assert sampler.read(tmp_path)["network_available"] is False
