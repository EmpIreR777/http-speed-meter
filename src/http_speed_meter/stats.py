import dataclasses
import json

from http_speed_meter.models import RequestMeasurement, SpeedReport

HEADER = f"{'#':>3}  {'Код':>4}  {'Байт':>12}  {'Время, с':>9}  {'МБ/с':>8}  {'Мбит/с':>8}"
SEPARATOR = "-" * len(HEADER)


def _thousands(value: float) -> str:
    """Отформатировать число, разделив тысячи неразрывным пробелом."""
    return f"{value:,.0f}".replace(",", "\u00a0")


def format_table_header() -> str:
    """Отрисовать заголовок таблицы с результатами отдельных запросов."""
    return f"{HEADER}\n{SEPARATOR}"


def format_measurement_line(measurement: RequestMeasurement) -> str:
    """Отрисовать результат одного запроса строкой таблицы."""
    return (
        f"{measurement.index:>3}  "
        f"{measurement.status_code:>4}  "
        f"{_thousands(measurement.bytes_downloaded):>12}  "
        f"{measurement.elapsed_seconds:>9.3f}  "
        f"{measurement.speed_mb_per_s:>8.2f}  "
        f"{measurement.speed_mbit_per_s:>8.2f}"
    )


def format_report(report: SpeedReport) -> str:
    """Отрисовать полный консольный отчёт: заголовок, таблицу и итоги."""
    lines = [
        f"Замер скорости для {report.url}",
        "",
        HEADER,
        SEPARATOR,
    ]
    lines.extend(format_measurement_line(item) for item in report.measurements)
    lines.append(SEPARATOR)
    return "\n".join([*lines, format_summary(report)])


def format_summary(report: SpeedReport) -> str:
    """Отрисовать только итоговую часть отчёта, без таблицы по запросам."""
    return "\n".join(
        [
            f"Выполнено запросов:    {report.request_count}",
            f"Скачано всего:         {_thousands(report.total_bytes)} байт "
            f"({report.total_bytes / 1_000_000:.2f} МБ)",
            f"Средний размер ответа: {_thousands(report.average_bytes)} байт",
            f"Среднее время запроса: {report.average_seconds:.3f} с "
            f"(мин. {report.min_seconds:.3f} с, макс. {report.max_seconds:.3f} с)",
            f"Суммарное время:       {report.total_seconds:.3f} с",
            "",
            "Средняя скорость:",
            f"  {report.average_speed_mb_per_s:.2f} МБ/с "
            f"({report.average_speed_mbit_per_s:.2f} Мбит/с)",
        ]
    )


def report_to_json(report: SpeedReport) -> str:
    """Отрисовать отчёт как JSON: машиночитаемый вывод для автоматизации."""
    payload = {
        "url": report.url,
        "requests": report.request_count,
        "total_bytes": report.total_bytes,
        "total_seconds": round(report.total_seconds, 6),
        "average_bytes": report.average_bytes,
        "average_seconds": round(report.average_seconds, 6),
        "min_seconds": round(report.min_seconds, 6),
        "max_seconds": round(report.max_seconds, 6),
        "average_speed_mb_per_s": round(report.average_speed_mb_per_s, 4),
        "average_speed_mbit_per_s": round(report.average_speed_mbit_per_s, 4),
        "measurements": [
            {**dataclasses.asdict(item), "speed_mb_per_s": item.speed_mb_per_s}
            for item in report.measurements
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
