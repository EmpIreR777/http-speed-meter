import sys
from collections.abc import Sequence

from http_speed_meter.cli import build_parser
from http_speed_meter.errors import ExitCode, MeasurementError, exit_code_for
from http_speed_meter.measure import run_speed_test
from http_speed_meter.models import RequestMeasurement
from http_speed_meter.stats import (
    SEPARATOR,
    format_measurement_line,
    format_summary,
    format_table_header,
    report_to_json,
)


def _print_measurement(measurement: RequestMeasurement) -> None:
    """Напечатать строку таблицы сразу после завершения очередного запроса."""
    print(format_measurement_line(measurement), flush=True)


def main(argv: Sequence[str] | None = None) -> int:
    """Точка входа консольной команды http-speed-meter.

    Возвращает код из :class: http_speed_meter.errors.ExitCode: 0 при успехе,
    иначе код, соответствующий причине сбоя.
    """
    args = build_parser().parse_args(argv)
    as_json: bool = args.as_json

    if not as_json:
        print(f"Замер скорости для {args.url}", flush=True)
        print(format_table_header(), flush=True)

    try:
        report = run_speed_test(
            args.url,
            requests=args.requests,
            timeout=args.timeout,
            on_progress=None if as_json else _print_measurement,
        )
    except MeasurementError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return exit_code_for(exc)
    except ValueError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return ExitCode.USAGE
    except KeyboardInterrupt:
        print("Прервано пользователем (Ctrl+C)", file=sys.stderr)
        return ExitCode.INTERRUPTED
    except Exception as exc:  # непредвиденному сбою нужен отдельный код возврата
        print(f"Непредвиденная ошибка {type(exc).__name__}: {exc}", file=sys.stderr)
        return ExitCode.FAILURE

    if as_json:
        print(report_to_json(report))
    else:
        print(SEPARATOR)
        print(format_summary(report))
    return ExitCode.OK


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
