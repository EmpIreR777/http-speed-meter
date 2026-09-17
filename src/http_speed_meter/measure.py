import time
from collections.abc import Callable

import httpx

from http_speed_meter.errors import (
    HTTPStatusMeasurementError,
    InvalidURLError,
    NetworkError,
    TimeoutMeasurementError,
)
from http_speed_meter.models import RequestMeasurement, SpeedReport

DEFAULT_REQUESTS: int = 10
DEFAULT_TIMEOUT_SECONDS: float = 30.0
DEFAULT_USER_AGENT: str = "http-speed-meter/0.1 (+https://github.com/EmpIreR777/http-speed-meter)"

ProgressCallback = Callable[[RequestMeasurement], None]


def measure_once(client: httpx.Client, url: str, *, index: int = 1) -> RequestMeasurement:
    """Выполнить один потоковый GET-запрос и замерить время и объём.

    Тело ответа вычитывается и выбрасывается: скрипту нужен только размер,
    а не сама картинка. Ошибки httpx превращаются в понятные ошибки замера,
    чтобы CLI мог вернуть осмысленный код возврата.
    """
    bytes_downloaded = 0
    started_at = time.perf_counter()
    try:
        with client.stream("GET", url) as response:
            response.raise_for_status()
            for chunk in response.iter_bytes(chunk_size=None):
                bytes_downloaded += len(chunk)
            status_code = response.status_code
    except (httpx.InvalidURL, httpx.UnsupportedProtocol) as exc:
        raise InvalidURLError(f"некорректный адрес {url!r}: {exc}") from exc
    except httpx.TimeoutException as exc:
        raise TimeoutMeasurementError(
            f"сервер не ответил по адресу {url} за отведённое время"
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPStatusMeasurementError(url, exc.response.status_code) from exc
    except httpx.HTTPError as exc:
        raise NetworkError(f"запрос к {url} не удался: {exc}") from exc
    elapsed_seconds = time.perf_counter() - started_at

    return RequestMeasurement(
        index=index,
        url=url,
        status_code=status_code,
        bytes_downloaded=bytes_downloaded,
        elapsed_seconds=elapsed_seconds,
    )


def run_speed_test(
    url: str,
    *,
    requests: int = DEFAULT_REQUESTS,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    on_progress: ProgressCallback | None = None,
) -> SpeedReport:
    """Сделать requests последовательных запросов и собрать отчёт.

    Запросы идут строго по очереди, чтобы каждый замер получал всю ширину канала.
    Завершённые замеры можно отрисовывать по мере поступления через on_progress.
    """
    if requests <= 0:
        raise ValueError("количество запросов должно быть положительным")

    measurements: list[RequestMeasurement] = []
    with httpx.Client(
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": DEFAULT_USER_AGENT},
    ) as client:
        for index in range(1, requests + 1):
            measurement = measure_once(client, url, index=index)
            measurements.append(measurement)
            if on_progress is not None:
                on_progress(measurement)

    return SpeedReport(url=url, measurements=tuple(measurements))
