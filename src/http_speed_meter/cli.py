import argparse

from http_speed_meter import __version__
from http_speed_meter.measure import DEFAULT_REQUESTS, DEFAULT_TIMEOUT_SECONDS

EPILOG = """\
Примеры:
  http-speed-meter -n 10 https://upload.wikimedia.org/wikipedia/commons/3/3d/LARGE_elevation.jpg
  http-speed-meter --json -n 3 https://proof.ovh.net/files/10Mb.dat

Коды возврата: 0 — успех, 2 — ошибка аргументов, 3 — некорректный адрес,
4 — сетевая ошибка, 5 — таймаут, 6 — неуспешный HTTP-статус, 130 — Ctrl+C."""


def build_parser() -> argparse.ArgumentParser:
    """Собрать парсер аргументов командной строки."""
    parser = argparse.ArgumentParser(
        prog="http-speed-meter",
        description=(
            "Измеряет скорость интернета: последовательно скачивает указанный адрес "
            "(например, тяжёлую картинку), замеряет время каждого запроса и печатает "
            "среднюю скорость."
        ),
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "url",
        help="адрес тяжёлого ресурса (большая картинка, файл с тестовыми данными)",
    )
    parser.add_argument(
        "-n",
        "--requests",
        type=int,
        default=DEFAULT_REQUESTS,
        metavar="N",
        help="количество последовательных запросов",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        metavar="СЕК",
        help="таймаут одного запроса в секундах",
    )
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="вывести результат в формате JSON (без промежуточных строк)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser
