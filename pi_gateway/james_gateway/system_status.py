from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import os
import re
import shutil
from typing import Mapping


_MACHINE_RE = re.compile(
    r"\b(pi|raspberry|titanium|gateway|server|system|machine)\b", re.IGNORECASE
)
_METRIC_RE = re.compile(
    r"\b(status|stats|health|temperature|thermal|hot|cpu|processor|load|"
    r"memory|ram|disk|storage|space|uptime|resources?|usage|used)\b",
    re.IGNORECASE,
)


def system_status_requested(text: str) -> bool:
    """Recognize an explicit request for this Pi's read-only operating metrics."""
    return bool(_MACHINE_RE.search(text) and _METRIC_RE.search(text))


@dataclass(frozen=True)
class SystemSnapshot:
    temperature_c: float | None
    fan_rpm: int | None
    fan_percent: float | None
    cooling_state: int | None
    cooling_max_state: int | None
    load_1m: float
    load_5m: float
    load_15m: float
    memory_used_gib: float
    memory_total_gib: float
    disk_used_gib: float
    disk_total_gib: float
    uptime_seconds: int

    def as_dict(self) -> dict[str, float | int | None]:
        return asdict(self)

    def describe(self, components: Mapping[str, object]) -> str:
        temperature = (
            f"The Pi is at {self.temperature_c:.1f} degrees Celsius. "
            if self.temperature_c is not None
            else "The Pi temperature sensor is unavailable. "
        )
        fan = ""
        if self.fan_rpm is not None:
            fan = f"The cooling fan is running at {self.fan_rpm} RPM"
            if self.fan_percent is not None:
                fan += f", about {self.fan_percent:.0f} percent PWM"
            if self.cooling_state is not None and self.cooling_max_state is not None:
                fan += f", at cooling state {self.cooling_state} of {self.cooling_max_state}"
            fan += ". "
        uptime_hours = self.uptime_seconds / 3600
        healthy = sorted(name for name, value in components.items() if bool(value))
        unhealthy = sorted(name for name, value in components.items() if not bool(value))
        services = (
            f"Healthy services: {', '.join(healthy)}. " if healthy else ""
        )
        if unhealthy:
            services += f"Services needing attention: {', '.join(unhealthy)}."
        return (
            f"{temperature}{fan}Load average is {self.load_1m:.2f}, {self.load_5m:.2f}, "
            f"and {self.load_15m:.2f}. Memory use is {self.memory_used_gib:.1f} "
            f"of {self.memory_total_gib:.1f} gibibytes; disk use is "
            f"{self.disk_used_gib:.1f} of {self.disk_total_gib:.1f} gibibytes. "
            f"Uptime is {uptime_hours:.1f} hours. {services}"
        ).strip()


class PiSystemStatus:
    """Read a fixed set of Linux metrics without invoking commands or writing state."""

    @staticmethod
    def _temperature() -> float | None:
        try:
            raw = Path("/sys/class/thermal/thermal_zone0/temp").read_text(
                encoding="ascii"
            ).strip()
            value = float(raw)
            return value / 1000 if value > 200 else value
        except (OSError, ValueError):
            return None

    @staticmethod
    def _memory() -> tuple[float, float]:
        values: dict[str, int] = {}
        for line in Path("/proc/meminfo").read_text(encoding="ascii").splitlines():
            key, raw = line.split(":", 1)
            values[key] = int(raw.strip().split()[0]) * 1024
        total = values["MemTotal"]
        available = values["MemAvailable"]
        return (total - available) / (1024**3), total / (1024**3)

    @staticmethod
    def _uptime() -> int:
        raw = Path("/proc/uptime").read_text(encoding="ascii").split()[0]
        return int(float(raw))

    @staticmethod
    def _optional_int(path: str) -> int | None:
        try:
            return int(Path(path).read_text(encoding="ascii").strip())
        except (OSError, ValueError):
            return None

    def snapshot(self) -> SystemSnapshot:
        load_1m, load_5m, load_15m = os.getloadavg()
        memory_used, memory_total = self._memory()
        disk = shutil.disk_usage("/")
        fan_rpm = self._optional_int("/sys/class/hwmon/hwmon3/fan1_input")
        fan_pwm = self._optional_int("/sys/class/hwmon/hwmon3/pwm1")
        return SystemSnapshot(
            temperature_c=self._temperature(),
            fan_rpm=fan_rpm,
            fan_percent=(fan_pwm / 255 * 100) if fan_pwm is not None else None,
            cooling_state=self._optional_int(
                "/sys/class/thermal/cooling_device0/cur_state"
            ),
            cooling_max_state=self._optional_int(
                "/sys/class/thermal/cooling_device0/max_state"
            ),
            load_1m=load_1m,
            load_5m=load_5m,
            load_15m=load_15m,
            memory_used_gib=memory_used,
            memory_total_gib=memory_total,
            disk_used_gib=disk.used / (1024**3),
            disk_total_gib=disk.total / (1024**3),
            uptime_seconds=self._uptime(),
        )
