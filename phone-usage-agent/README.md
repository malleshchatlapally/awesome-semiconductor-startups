# Phone usage agent

Small local agent that **only counts time while you are actively using your phone**, then alerts you to take a break every **30 minutes** (configurable).

## How it works

1. Polls every ~15 seconds to see if the phone is in use.
2. **iPhone (default):** your phone sends **heartbeats** via the Shortcuts app to this agent on your Mac (same Wi‑Fi). See [`ios/README.md`](ios/README.md).
3. **Android (optional):** screen on and unlocked via **ADB** on a connected computer.
4. When you hit 30 minutes of active use, you get an alert on your **iPhone** (next heartbeat) and on your **computer**.
5. If heartbeats stop for ~2 minutes, the timer resets.

## Requirements

- Python 3.9+
- **iPhone:** Mac or PC on the same network running this agent; iOS **Shortcuts** (setup in [`ios/README.md`](ios/README.md)).
- **Android (optional):** [ADB](https://developer.android.com/tools/adb), USB or wireless debugging.

## Quick start (iPhone)

```bash
cd phone-usage-agent
mkdir -p ~/.config/phone-usage-agent
cp config.example.json ~/.config/phone-usage-agent/config.json
# Edit secret + save
python3 agent.py
```

Then follow **[iPhone Shortcuts setup](ios/README.md)** (heartbeat loop in Control Center).

```bash
# Test without an iPhone (fake heartbeats)
python3 agent.py --backend simulate --interval 1 -v

# Android instead
python3 agent.py --backend adb
```

## Configuration

| Field | Default | Meaning |
|-------|---------|---------|
| `interval_minutes` | 30 | Alert after this much **active** use |
| `poll_seconds` | 15 | How often the agent checks state |
| `idle_reset_minutes` | 2 | No heartbeats this long → reset timer |
| `backend` | `iphone` | `iphone`, `adb`, `simulate`, or `manual` |
| `iphone.port` | 8765 | HTTP port for Shortcuts POST |
| `iphone.secret` | (required) | Bearer token in Shortcut headers |
| `iphone.heartbeat_stale_seconds` | 45 | No heartbeat this long → not “in use” |
| `iphone.alert_on_iphone` | true | Queue notification for next heartbeat |

## Run in the background (macOS launchd)

```xml
<!-- ~/Library/LaunchAgents/com.phone-usage-agent.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.phone-usage-agent</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>/FULL/PATH/phone-usage-agent/agent.py</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
</dict>
</plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.phone-usage-agent.plist
```

## Android setup

1. **Settings → Developer options → USB debugging** on the phone.
2. `adb devices` on the computer; accept the RSA prompt.
3. `python3 agent.py --backend adb`

## License

Use and modify freely.
