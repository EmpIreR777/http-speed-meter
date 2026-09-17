from dataclasses import dataclass
from typing import Final

BYTES_PER_MEGABYTE: Final = 1_000_000
BITS_PER_BYTE: Final = 8


@dataclass(frozen=True, slots=True)
class RequestMeasurement:
    """Результат одного завершённого HTTP-запроса."""

    index: int
    url: str
    status_code: int
    bytes_downloaded: int
    elapsed_seconds: float

    @property
    def speed_mb_per_s(self) -> float:
        """Скорость скачивания этого запроса в мегабайтах в секунду."""
        return speed_mb_per_s(self.bytes_downloaded, self.elapsed_seconds)

    @property
    def speed_mbit_per_s(self) -> float:
        """Скорость скачивания этого запроса в мегабитах в секунду."""
        return self.speed_mb_per_s * BITS_PER_BYTE


@dataclass(frozen=True, slots=True)
class SpeedReport:
    """Итог серии последовательных замеров."""

    url: str
    measurements: tuple[RequestMeasurement, ...]

    @property
    def request_count(self) -> int:
        """Количество замеренных запросов."""
        return len(self.measurements)

    @property
    def total_bytes(self) -> int:
        """Суммарный объём скачанных данных в байтах."""
        return sum(item.bytes_downloaded for item in self.measurements)

    @property
    def total_seconds(self) -> float:
        """Суммарное время ожидания всех ответов в секундах."""
        return sum(item.elapsed_seconds for item in self.measurements)

    @property
    def average_bytes(self) -> float:
        """Средний размер одного ответа в байтах."""
        return self.total_bytes / self.request_count

    @property
    def average_seconds(self) -> float:
        """Среднее время одного запроса в секундах."""
        return self.total_seconds / self.request_count

    @property
    def min_seconds(self) -> float:
        """Время самого быстрого запроса в секундах."""
        return min(item.elapsed_seconds for item in self.measurements)

    @property
    def max_seconds(self) -> float:
        """Время самого медленного запроса в секундах."""
        return max(item.elapsed_seconds for item in self.measurements)

    @property
    def average_speed_mb_per_s(self) -> float:
        """Средняя скорость в МБ/с: весь объём, делённый на всё время."""
        return speed_mb_per_s(self.total_bytes, self.total_seconds)

    @property
    def average_speed_mbit_per_s(self) -> float:
        """Средняя скорость в Мбит/с."""
        return self.average_speed_mb_per_s * BITS_PER_BYTE


def speed_mb_per_s(bytes_downloaded: int, elapsed_seconds: float) -> float:
    """Перевести байты и время в МБ/с; при нулевом времени вернуть 0."""
    if elapsed_seconds <= 0:
        return 0.0
    return bytes_downloaded / BYTES_PER_MEGABYTE / elapsed_seconds
