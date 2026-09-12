# Phone usage agent

Small local agent that **only counts time while you are actively using your phone**, then alerts you to take a break every **30 minutes** (configurable).

## How it works

1. Polls every ~15 seconds to see if the phone is in use.
2. **Android (ADB):** screen on and not on the lock screen.
3. Accumulates active-use seconds; when you hit 30 minutes, you get a desktop notification (or terminal bell).
4. If the phone stays idle (screen off) for 2 minutes, the timer resets so breaks do not count against you.

## Requirements

- Python 3.9+
- **Android:** [ADB](https://developer.android.com/tools/adb) on your computer, USB debugging or wireless debugging enabled, phone authorized (`adb devices` shows `device`).

Linux desktop alerts use `notify-send` (install `libnotify-bin` on Debian/Ubuntu). macOS uses Notification Center; Windows uses a toast when possible.

## Quick start

```bash
cd phone-usage-agent
python3 agent.py
```

First run with defaults uses the `adb` backend. Override on the command line:

```bash
# Alert every 20 minutes
python3 agent.py --interval 20

# Test without a phone (cycles fake "in use" / idle)
python3 agent.py --backend simulate --interval 1 -v

# Toggle usage yourself (Enter = start/stop)
python3 agent.py --backend manual --interval 1 -v
```

## Configuration

Copy the example config:

```bash
mkdir -p ~/.config/phone-usage-agent
cp config.example.json ~/.config/phone-usage-agent/config.json
```

| Field | Default | Meaning |
|-------|---------|---------|
| `interval_minutes` | 30 | Alert after this much **active** use |
| `poll_seconds` | 15 | How often to check phone state |
| `idle_reset_minutes` | 2 | Screen off this long → reset timer |
| `backend` | `adb` | `adb`, `simulate`, or `manual` |
| `alert_title` / `alert_message` | see file | Notification text |

## Android setup

1. On the phone: **Settings → Developer options → USB debugging** (on).
2. Connect USB or pair [wireless debugging](https://developer.android.com/tools/adb#wireless-android11).
3. On the computer: `adb devices` and accept the RSA prompt on the phone.
4. Run `python3 agent.py` and leave it in a terminal or run under `systemd`/launchd.

### Run in the background (Linux systemd user unit)

```ini
# ~/.config/systemd/user/phone-usage-agent.service
[Unit]
Description=Phone usage break reminders

[Service]
ExecStart=%h/path/to/phone-usage-agent/agent.py
Restart=on-failure

[Install]
WantedBy=default.target
```

```bash
systemctl --user enable --now phone-usage-agent.service
```

## iPhone

iOS does not expose the same ADB-style signals to a PC. Practical options:

- Use **Screen Time → App Limits** or **Downtime** in Settings.
- Or run a Shortcuts automation on a schedule (not true “only while using” detection).

This agent is aimed at **Android + desktop** today; an iOS companion would need a small native app or Shortcuts integration.

## License

Use and modify freely.
