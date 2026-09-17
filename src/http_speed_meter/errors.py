from enum import IntEnum


class MeasurementError(RuntimeError):
    """Базовая ошибка замера: запрос не удалось выполнить."""


class InvalidURLError(MeasurementError):
    """Адрес некорректен: нет схемы или протокол не поддерживается."""


class NetworkError(MeasurementError):
    """Сетевая ошибка: DNS, соединение, TLS, обрыв соединения."""


class TimeoutMeasurementError(NetworkError):
    """Сервер не ответил или не прислал данные за отведённое время."""


class HTTPStatusMeasurementError(MeasurementError):
    """Сервер ответил неуспешным HTTP-статусом (не 2xx)."""

    url: str
    status_code: int

    def __init__(self, url: str, status_code: int) -> None:
        """Сохранить адрес и статус, чтобы CLI мог показать понятное сообщение."""
        super().__init__(f"сервер вернул {status_code} для {url}")
        self.url = url
        self.status_code = status_code


class ExitCode(IntEnum):
    """Коды возврата процесса (описаны в README, раздел «Коды возврата»)."""

    OK = 0  # замер выполнен, отчёт напечатан
    FAILURE = 1  # непредвиденная ошибка, не из перечисленных ниже
    USAGE = 2  # ошибка в аргументах командной строки (тот же код и у argparse)
    INVALID_URL = 3  # некорректный адрес или неподдерживаемый протокол
    NETWORK = 4  # сетевая ошибка: DNS, соединение, TLS
    TIMEOUT = 5  # сервер не ответил за отведённое время
    HTTP_STATUS = 6  # неуспешный HTTP-статус (не 2xx)
    INTERRUPTED = 130  # прерывание по Ctrl+C, канонический код 128 + SIGINT


def exit_code_for(error: MeasurementError) -> ExitCode:
    """Подобрать код возврата под конкретный тип ошибки замера."""
    if isinstance(error, HTTPStatusMeasurementError):
        return ExitCode.HTTP_STATUS
    if isinstance(error, TimeoutMeasurementError):
        return ExitCode.TIMEOUT
    if isinstance(error, InvalidURLError):
        return ExitCode.INVALID_URL
    if isinstance(error, NetworkError):
        return ExitCode.NETWORK
    return ExitCode.FAILURE
