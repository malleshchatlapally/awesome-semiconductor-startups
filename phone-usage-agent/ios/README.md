# iPhone setup (Shortcuts)

Apple does not allow a PC to read “screen on” from an iPhone the way ADB does on Android. This agent uses **Shortcuts on your iPhone** to send **heartbeats** to the Python agent on your Mac (or any computer on the same Wi‑Fi).

## 1. Run the agent on your Mac

```bash
cd phone-usage-agent
cp config.example.json ~/.config/phone-usage-agent/config.json
# Edit: set backend to "iphone", set iphone.secret, note iphone.port
python3 agent.py --backend iphone
```

Leave this running. The agent listens on port **8765** by default (`0.0.0.0` so your phone can reach it).

Find your Mac’s LAN IP: **System Settings → Network** (e.g. `192.168.1.42`).

## 2. Create the “Phone Agent Heartbeat” shortcut

In the **Shortcuts** app on iPhone:

1. **New Shortcut** → name it `Phone Agent Heartbeat`.
2. Add actions in order:

| Step | Action | Settings |
|------|--------|----------|
| 1 | **Text** | `http://YOUR_MAC_IP:8765/v1/heartbeat` (replace IP) |
| 2 | **Get Contents of URL** | Method: **POST**; Headers: `Authorization` = `Bearer YOUR_SECRET` (same as `iphone.secret` in config) |
| 3 | **Get Dictionary from Input** | Input = result of step 2 |
| 4 | **If** | Dictionary `notify` is `true` |
| 5 | **Show Notification** | Title = Dictionary `title`; Body = Dictionary `message` |
| 6 | **End If** | |
| 7 | **Wait** | 30 seconds |
| 8 | **Run Shortcut** | `Phone Agent Heartbeat` (creates a loop) |

3. Turn off **Ask Before Running** when prompted (for the self-loop).

Pin this shortcut to **Control Center** (Settings → Control Center → add Shortcuts).

**How to use:** When you start using your phone, run **Phone Agent Heartbeat** once from Control Center. It pings every 30s while the shortcut runs. When you stop, swipe away the shortcut or lock the phone (the loop pauses; heartbeats stop and the agent resets after ~2 minutes idle).

> **Tip:** Assign **Back Tap** (Settings → Accessibility → Touch → Back Tap) to run this shortcut so starting a session is one double-tap.

## 3. Optional: ping when you open apps

For apps where you forget to start the loop, add **Personal Automations**:

1. Shortcuts → **Automation** → **+** → **App** → choose apps (e.g. Instagram, Safari).
2. Trigger: **Is Opened**; run immediately.
3. Action: **Get Contents of URL** — same POST URL and `Authorization` header as above (no loop).
4. Disable **Ask Before Running**.

Opening those apps counts as active use until heartbeats go stale (~45s without another open or loop tick).

## 4. Security

- Use a long random `iphone.secret` in config.
- Prefer your home Wi‑Fi; do not expose port 8765 to the public internet without TLS and a reverse proxy.

## 5. Test from a computer

```bash
curl -s -X POST http://127.0.0.1:8765/v1/heartbeat \
  -H "Authorization: Bearer YOUR_SECRET"
```

With the agent running and `--backend iphone`, repeated curls simulate active use.

## Native Screen Time (no agent)

If you only need a 30‑minute cap with no Mac running: **Settings → Screen Time → App Limits** and set a 30‑minute daily limit per category. The agent is for custom messages and “active use only” with a heartbeat loop.
