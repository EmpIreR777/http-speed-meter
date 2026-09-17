import socket
import threading
import time
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

PAYLOAD_SIZE = 64 * 1024
PAYLOAD = bytes(range(256)) * (PAYLOAD_SIZE // 256)
RESOURCE_PATH = "/heavy-image.jpg"
SLOW_PATH = "/slow"
SLOW_DELAY_SECONDS = 0.5
NOT_FOUND_PATH = "/not-found"


class _HeavyResourceHandler(BaseHTTPRequestHandler):
    """Отдавать бинарный ресурс, медленный ответ и ошибку 404."""

    protocol_version = "HTTP/1.1"
    server_version = "TestHTTP/1.1"

    def do_GET(self) -> None:
        if self.path == RESOURCE_PATH:
            self._send_payload()
        elif self.path == SLOW_PATH:
            time.sleep(SLOW_DELAY_SECONDS)
            self._send_payload()
        elif self.path == NOT_FOUND_PATH:
            self.send_error(404, "Not Found")
        else:
            self.send_error(500, "Unexpected path")

    def _send_payload(self) -> None:
        """Отправить полезную нагрузку, не падая при уже закрытом клиенте."""
        try:
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(PAYLOAD)))
            self.end_headers()
            self.wfile.write(PAYLOAD)
        except BrokenPipeError, ConnectionResetError:
            # Клиент ушёл раньше нас (например, сработал таймаут) — в тестах это норма.
            pass

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        """Не засорять вывод тестов сообщениями сервера."""


@pytest.fixture(scope="session")
def heavy_server() -> Iterator[str]:
    """Поднять локальный HTTP-сервер и отдать его базовый адрес."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), _HeavyResourceHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    try:
        yield f"http://{host!s}:{port!s}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.fixture(scope="session")
def heavy_url(heavy_server: str) -> str:
    """Адрес «тяжёлого» ресурса на локальном сервере."""
    return f"{heavy_server}{RESOURCE_PATH}"


@pytest.fixture(scope="session")
def slow_url(heavy_server: str) -> str:
    """Адрес, который отвечает медленнее, чем таймаут в тестах на таймаут."""
    return f"{heavy_server}{SLOW_PATH}"


@pytest.fixture(scope="session")
def not_found_url(heavy_server: str) -> str:
    """Адрес, на который сервер отвечает статусом 404."""
    return f"{heavy_server}{NOT_FOUND_PATH}"


@pytest.fixture(scope="session")
def closed_port_url() -> str:
    """Адрес закрытого порта: даёт мгновенную сетевую ошибку подключения."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    return f"http://127.0.0.1:{port}/heavy-image.jpg"
