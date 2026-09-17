import json

import pytest

from http_speed_meter import __version__
from http_speed_meter.errors import ExitCode
from http_speed_meter.main import main

from .conftest import PAYLOAD


def test_main_prints_console_report(
    heavy_url: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main([heavy_url, "-n", "2", "-t", "10"])

    captured = capsys.readouterr()
    assert exit_code == ExitCode.OK
    assert "Замер скорости для" in captured.out
    assert "Выполнено запросов:    2" in captured.out
    assert "Средняя скорость:" in captured.out
    assert captured.err == ""


def test_main_supports_json_output(
    heavy_url: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["--json", "-n", "2", heavy_url])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == ExitCode.OK
    assert payload["url"] == heavy_url
    assert payload["requests"] == 2
    assert payload["total_bytes"] == len(PAYLOAD) * 2


def test_main_returns_http_status_code(
    not_found_url: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main([not_found_url, "-n", "1"])

    assert exit_code == ExitCode.HTTP_STATUS
    assert "404" in capsys.readouterr().err


def test_main_returns_invalid_url_code(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["not-a-url", "-n", "1"])

    assert exit_code == ExitCode.INVALID_URL
    assert "некорректный адрес" in capsys.readouterr().err


def test_main_returns_network_code(
    closed_port_url: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main([closed_port_url, "-n", "1", "-t", "2"])

    assert exit_code == ExitCode.NETWORK
    assert "Ошибка" in capsys.readouterr().err


def test_main_returns_timeout_code(slow_url: str) -> None:
    exit_code = main([slow_url, "-n", "1", "-t", "0.05"])

    assert exit_code == ExitCode.TIMEOUT


def test_main_returns_usage_code_for_zero_requests(
    heavy_url: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main([heavy_url, "-n", "0"])

    assert exit_code == ExitCode.USAGE
    assert "положительным" in capsys.readouterr().err


def test_main_rejects_unknown_option() -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--unknown-option"])

    assert exc_info.value.code == ExitCode.USAGE


def test_main_prints_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])

    assert exc_info.value.code == ExitCode.OK
    assert __version__ in capsys.readouterr().out


def test_exit_codes_are_unique_and_stable() -> None:
    values = [code.value for code in ExitCode]

    assert len(values) == len(set(values))
    assert ExitCode.OK.value == 0
    assert ExitCode.INTERRUPTED.value == 130
