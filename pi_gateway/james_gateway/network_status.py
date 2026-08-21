from __future__ import annotations

from dataclasses import asdict, dataclass
import socket
import time


@dataclass(frozen=True)
class NetworkSnapshot:
    local_hostname: str
    dns_ok: bool
    internet_tcp_ok: bool
    internet_latency_ms: int | None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)

    def describe(self) -> str:
        dns = "DNS resolution is working" if self.dns_ok else "DNS resolution failed"
        if self.internet_tcp_ok:
            internet = f"an outbound internet connection succeeded in about {self.internet_latency_ms} milliseconds"
        else:
            internet = "the bounded outbound internet probe failed"
        return f"Network check from {self.local_hostname}: {dns}, and {internet}."


class NetworkStatus:
    """Fixed read-only LAN/DNS/internet probes; no command execution."""

    def snapshot(self, timeout: float = 2.0) -> NetworkSnapshot:
        hostname = socket.gethostname()
        try:
            socket.getaddrinfo("example.com", 443, type=socket.SOCK_STREAM)
            dns_ok = True
        except OSError:
            dns_ok = False
        started = time.perf_counter()
        try:
            connection = socket.create_connection(("1.1.1.1", 443), timeout=timeout)
            connection.close()
            tcp_ok = True
            latency = round((time.perf_counter() - started) * 1000)
        except OSError:
            tcp_ok = False
            latency = None
        return NetworkSnapshot(hostname, dns_ok, tcp_ok, latency)
