#!/usr/bin/env python3
"""
Phone usage agent: tracks active phone use and alerts every N minutes.

Backends:
  adb       - Android phone connected via USB/Wi‑Fi debugging (default)
  simulate  - For testing: toggles "in use" on a timer
  manual    - stdin: press Enter when you start/stop using the phone
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "phone-usage-agent" / "config.json"


@dataclass
class Config:
    interval_minutes: int = 30
    poll_seconds: float = 15.0
    idle_reset_minutes: float = 2.0
    backend: str = "adb"
    alert_title: str = "Phone break"
    alert_message: str = (
        "You've been on your phone for 30 minutes. Time to put it down."
    )

    @classmethod
    def load(cls, path: Optional[Path]) -> "Config":
        if path and path.is_file():
            data = json.loads(path.read_text())
            return cls(
                interval_minutes=int(data.get("interval_minutes", 30)),
                poll_seconds=float(data.get("poll_seconds", 15)),
                idle_reset_minutes=float(data.get("idle_reset_minutes", 2)),
                backend=str(data.get("backend", "adb")),
                alert_title=str(data.get("alert_title", cls.alert_title)),
                alert_message=str(
                    data.get("alert_message", cls().alert_message)
                ),
            )
        return cls()


def notify(title: str, message: str) -> None:
    """Best-effort desktop (or terminal) alert."""
    system = platform.system()
    if system == "Linux" and shutil.which("notify-send"):
        subprocess.run(
            ["notify-send", "-u", "critical", title, message],
            check=False,
        )
        return
    if system == "Darwin":
        script = (
            f'display notification "{message}" with title "{title}" sound name "Glass"'
        )
        subprocess.run(["osascript", "-e", script], check=False)
        return
    if system == "Windows" and shutil.which("powershell"):
        ps = (
            "[Windows.UI.Notifications.ToastNotificationManager, "
            "Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null; "
            "$t = [Windows.UI.Notifications.ToastNotificationManager]::"
            "CreateToastNotifier('Phone Usage Agent'); "
            f"$xml = New-Object Windows.Data.Xml.Dom.XmlDocument; "
            f"$xml.LoadXml('<toast><visual><binding template=\"ToastText02\">"
            f"<text id=\"1\">{title}</text><text id=\"2\">{message}</text>"
            f"</binding></visual></toast>'); "
            "$t.Show([Windows.UI.Notifications.ToastNotification]::new($xml))"
        )
        subprocess.run(["powershell", "-Command", ps], check=False)
        return
    print(f"\n*** {title}: {message} ***\n", flush=True)
    sys.stdout.write("\a")
    sys.stdout.flush()


def adb_available() -> bool:
    return shutil.which("adb") is not None


def _adb_shell(command: str, timeout: float = 10.0) -> str:
    result = subprocess.run(
        ["adb", "shell", command],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        return ""
    return result.stdout or ""


def adb_device_ready() -> bool:
    if not adb_available():
        return False
    out = subprocess.run(
        ["adb", "devices"],
        capture_output=True,
        text=True,
        timeout=10,
    ).stdout
    lines = [ln.strip() for ln in out.splitlines()[1:] if ln.strip()]
    return any(ln.endswith("\tdevice") for ln in lines)


def phone_in_use_adb() -> bool:
    if not adb_device_ready():
        return False
    power = _adb_shell("dumpsys power")
    screen_on = (
        "Display Power: state=ON" in power
        or "mWakefulness=Awake" in power
        or "state=ON" in power and "Display" in power
    )
    if not screen_on:
        return False
    window = _adb_shell("dumpsys window")
    if "mDreamingLockscreen=true" in window:
        return False
    if "mShowingLockscreen=true" in window:
        return False
    return True


class SimulateBackend:
    """Alternates using / not using for demos."""

    def __init__(self, on_seconds: float = 120.0, off_seconds: float = 60.0) -> None:
        self.on_seconds = on_seconds
        self.off_seconds = off_seconds
        self._started = time.monotonic()

    def in_use(self) -> bool:
        t = time.monotonic() - self._started
        cycle = self.on_seconds + self.off_seconds
        phase = t % cycle
        return phase < self.on_seconds


class ManualBackend:
    """Toggle with Enter key (start using / stop using)."""

    def __init__(self) -> None:
        self._using = False
        print(
            "Manual mode: press Enter to toggle phone use on/off. Ctrl+C to quit.",
            flush=True,
        )

    def in_use(self) -> bool:
        return self._using

    def poll_toggle(self) -> None:
        import select

        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            sys.stdin.readline()
            self._using = not self._using
            state = "USING" if self._using else "not using"
            print(f"  → Phone: {state}", flush=True)


def make_detector(cfg: Config, args: argparse.Namespace) -> Callable[[], bool]:
    if cfg.backend == "simulate":
        sim = SimulateBackend(
            on_seconds=args.simulate_on,
            off_seconds=args.simulate_off,
        )
        return sim.in_use
    if cfg.backend == "manual":
        manual = ManualBackend()
        manual.poll_toggle()

        def _check() -> bool:
            manual.poll_toggle()
            return manual.in_use()

        return _check
    if cfg.backend == "adb":
        return phone_in_use_adb
    raise SystemExit(f"Unknown backend: {cfg.backend}")


def run_agent(cfg: Config, args: argparse.Namespace) -> None:
    interval_sec = cfg.interval_minutes * 60
    idle_reset_sec = cfg.idle_reset_minutes * 60
    in_use = make_detector(cfg, args)

    active_seconds = 0.0
    idle_seconds = 0.0
    last_tick = time.monotonic()
    alerted_blocks = 0

    print(
        f"Phone usage agent started (backend={cfg.backend}, "
        f"alert every {cfg.interval_minutes} min of active use).",
        flush=True,
    )
    if cfg.backend == "adb" and not adb_device_ready():
        print(
            "Warning: no adb device in 'device' state. "
            "Enable USB debugging and run: adb devices",
            flush=True,
        )

    try:
        while True:
            now = time.monotonic()
            dt = now - last_tick
            last_tick = now

            using = in_use()
            if using:
                idle_seconds = 0.0
                active_seconds += dt
            else:
                idle_seconds += dt
                if idle_seconds >= idle_reset_sec:
                    if active_seconds > 0:
                        print(
                            f"  Idle {cfg.idle_reset_minutes:.0f} min — "
                            "resetting usage timer.",
                            flush=True,
                        )
                    active_seconds = 0.0
                    alerted_blocks = 0

            while active_seconds >= interval_sec:
                alerted_blocks += 1
                n = cfg.interval_minutes
                unit = "minute" if n == 1 else "minutes"
                msg = cfg.alert_message.replace("30 minutes", f"{n} {unit}")
                if "30 minutes" not in cfg.alert_message:
                    msg = f"{cfg.alert_message} ({n} {unit} of use)."
                notify(cfg.alert_title, msg)
                print(
                    f"  Alert #{alerted_blocks} "
                    f"({cfg.interval_minutes} min active use).",
                    flush=True,
                )
                active_seconds -= interval_sec

            if args.verbose:
                status = "using" if using else "idle"
                print(
                    f"  [{status}] active={active_seconds:.0f}s "
                    f"(next alert in {max(0, interval_sec - active_seconds):.0f}s)",
                    flush=True,
                )

            time.sleep(cfg.poll_seconds)
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Alert after N minutes of phone use.")
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH if DEFAULT_CONFIG_PATH.is_file() else None,
        help="Path to config JSON (default: ~/.config/phone-usage-agent/config.json)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help="Override interval in minutes",
    )
    parser.add_argument(
        "--backend",
        choices=("adb", "simulate", "manual"),
        default=None,
        help="Detection backend",
    )
    parser.add_argument(
        "--simulate-on",
        type=float,
        default=120.0,
        help="Simulate: seconds 'in use' per cycle",
    )
    parser.add_argument(
        "--simulate-off",
        type=float,
        default=60.0,
        help="Simulate: seconds idle per cycle",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    cfg = Config.load(args.config)
    if args.interval is not None:
        cfg.interval_minutes = args.interval
    if args.backend is not None:
        cfg.backend = args.backend

    run_agent(cfg, args)


if __name__ == "__main__":
    main()
