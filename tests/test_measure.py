import json

import httpx
import pytest

from http_speed_meter.errors import (
    HTTPStatusMeasurementError,
    InvalidURLError,
    NetworkError,
    TimeoutMeasurementError,
)
from http_speed_meter.measure import measure_once, run_speed_test
from http_speed_meter.models import RequestMeasurement, SpeedReport, speed_mb_per_s
from http_speed_meter.stats import format_report, report_to_json

from .conftest import PAYLOAD

URL = "https://example.com/heavy-image.jpg"


def make_measurement(
    index: int,
    *,
    size: int = 1_000_000,
    elapsed: float = 0.5,
) -> RequestMeasurement:
    """Собрать замер с заданными размером ответа и временем."""
    return RequestMeasurement(
        index=index,
        url=URL,
        status_code=200,
        bytes_downloaded=size,
        elapsed_seconds=elapsed,
    )


def test_measure_once_downloads_full_payload(heavy_url: str) -> None:
    with httpx.Client(timeout=10.0, follow_redirects=True) as client:
        measurement = measure_once(client, heavy_url)

    assert measurement.status_code == 200
    assert measurement.bytes_downloaded == len(PAYLOAD)
    assert measurement.elapsed_seconds > 0
    assert measurement.speed_mb_per_s > 0


def test_measure_once_maps_http_status_to_error(not_found_url: str) -> None:
    with httpx.Client(timeout=10.0) as client, pytest.raises(HTTPStatusMeasurementError) as exc:
        measure_once(client, not_found_url)

    assert exc.value.status_code == 404
    assert not_found_url in str(exc.value)


def test_measure_once_maps_timeout(slow_url: str) -> None:
    with httpx.Client(timeout=0.05) as client, pytest.raises(TimeoutMeasurementError):
        measure_once(client, slow_url)


def test_measure_once_maps_network_error(closed_port_url: str) -> None:
    with httpx.Client(timeout=2.0) as client, pytest.raises(NetworkError):
        measure_once(client, closed_port_url)


@pytest.mark.parametrize("url", ["not-a-url", "ftp://example.com/image.jpg"])
def test_measure_once_maps_invalid_url(url: str) -> None:
    with httpx.Client(timeout=10.0) as client, pytest.raises(InvalidURLError):
        measure_once(client, url)


def test_run_speed_test_collects_all_requests(heavy_url: str) -> None:
    report = run_speed_test(heavy_url, requests=3, timeout=10.0)

    assert [item.index for item in report.measurements] == [1, 2, 3]
    assert report.request_count == 3
    assert report.total_bytes == len(PAYLOAD) * 3
    assert report.average_bytes == pytest.approx(len(PAYLOAD))
    assert report.average_speed_mb_per_s > 0


def test_run_speed_test_reports_progress(heavy_url: str) -> None:
    progress: list[RequestMeasurement] = []

    report = run_speed_test(heavy_url, requests=2, timeout=10.0, on_progress=progress.append)

    assert report.request_count == 2
    assert [item.index for item in progress] == [1, 2]


@pytest.mark.parametrize("requests", [0, -1])
def test_run_speed_test_rejects_non_positive_requests(heavy_url: str, requests: int) -> None:
    with pytest.raises(ValueError, match="положительным"):
        run_speed_test(heavy_url, requests=requests)


def test_speed_units_are_decimal() -> None:
    measurement = make_measurement(1, size=1_000_000, elapsed=0.5)

    assert speed_mb_per_s(1_000_000, 0.0) == 0.0
    assert measurement.speed_mb_per_s == pytest.approx(2.0)
    assert measurement.speed_mbit_per_s == pytest.approx(16.0)


def test_report_aggregates_measurements() -> None:
    report = SpeedReport(
        url=URL,
        measurements=(
            make_measurement(1, size=1_000_000, elapsed=0.5),
            make_measurement(2, size=2_000_000, elapsed=1.5),
        ),
    )

    assert (report.request_count, report.total_bytes) == (2, 3_000_000)
    assert report.average_bytes == pytest.approx(1_500_000)
    assert report.average_seconds == pytest.approx(1.0)
    assert report.min_seconds == pytest.approx(0.5)
    assert report.max_seconds == pytest.approx(1.5)
    assert report.average_speed_mb_per_s == pytest.approx(1.5)
    assert report.average_speed_mbit_per_s == pytest.approx(12.0)


def test_format_report_contains_summary_and_units() -> None:
    text = format_report(SpeedReport(url=URL, measurements=(make_measurement(1),)))

    assert URL in text
    assert "Выполнено запросов:" in text
    assert "Среднее время запроса: 0.500 с" in text
    assert "2.00 МБ/с" in text


def test_report_to_json_is_machine_readable() -> None:
    report = SpeedReport(
        url=URL,
        measurements=(make_measurement(1), make_measurement(2, size=2_000_000, elapsed=1.0)),
    )

    payload = json.loads(report_to_json(report))

    assert payload["requests"] == 2
    assert payload["total_bytes"] == 3_000_000
    assert payload["average_seconds"] == pytest.approx(0.75)
    assert payload["measurements"][0]["speed_mb_per_s"] == pytest.approx(2.0)
