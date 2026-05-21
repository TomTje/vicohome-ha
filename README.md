![VicoHome Banner](custom_components/vicohome/brand/banner.png)

## VicoHome for Home Assistant

Custom integration for **VicoHome CG1** cloud cameras in Home Assistant.

> ⚠️ **Unofficial & community-driven.** This integration uses the undocumented VicoHome cloud API. VicoHome may change or restrict access at any time. Use at your own risk.

### Beta Testing & Feedback 🧪

We are actively looking for testers with different VicoHome models and regions.

- **Found a bug?** Open an [issue](https://github.com/TomTje/vicohome-ha/issues).
- **Want a feature?** Open a [discussion](https://github.com/TomTje/vicohome-ha/discussions).
- **General chat:** DM `@TomTje` on GitHub.

> 🔒 **Security:** All credentials (email, password, Telegram bot token) are entered **only via the Home Assistant UI** and stored in Home Assistant's encrypted internal `.storage`. **Nothing is hardcoded in this repository.**

### Features

- 📹 **Motion Detection** via cloud events (no local stream)
- 📸 **Snapshot Camera** entity showing the last motion event image
- 🖼️ **Event Image** entity for the latest event photo (downloadable)
- 📊 **Sensors**: event count (1h), last event details, battery, signal strength, IP, firmware, status
- 🔔 **Telegram Notifications** with photo + video (configurable)
- ⚙️ **Runtime settings** via HA UI: notification toggle, polling interval, Telegram bot/token
- 🎛️ **Buttons**: Manual snapshot, force refresh, restart device *(planned)*
- 💾 **Persistent serial cache** — survives Home Assistant restarts

### Requirements

- Home Assistant 2024.0.0 or newer
- VicoHome account (e-mail + password)
- ffmpeg (pre-installed in HA OS / Docker; for bare-metal: `apt install ffmpeg`)

### Installation

#### HACS (recommended)
1. Add the repository as a custom repository in HACS:
   - Go to **HACS → Integrations**
   - Click **⋮ → Custom repositories**
   - URL: `https://github.com/TomTje/vicohome-ha`
   - Category: **Integration**
2. Search for **VicoHome** and install.
3. Restart Home Assistant.

#### Manual
1. Download the `custom_components/vicohome` folder.
2. Copy it into `config/custom_components/vicohome`.
3. Restart Home Assistant.

#### Configuration
1. Go to **Settings → Devices & Services → Add Integration**.
2. Select **VicoHome** (or search for it).
3. Enter:
   - **E-Mail**
   - **Password**
   - **Region** (EU or US)
   - **Polling Interval** (default: 180 s)
4. After setup, use the new entities to configure Telegram:
  - `switch.vicohome_notifications` — ON/OFF
  - `text.vicohome_telegram_bot_token` — your Telegram bot token
  - `text.vicohome_telegram_recipient_id` — your Telegram chat ID
  - `number.vicohome_polling_interval` — seconds (60–3600)

### Supported Devices

| Model | Status |
|---|---|
| CG1 | ✅ Tested & confirmed |
| Other VicoHome models | ❓ Not tested yet — open an issue if you try one. |

### Entities

| Entity | Type | Description |
|---|---|---|
| `sensor.vicohome_events_1h` | Sensor | Number of events in the last hour |
| `sensor.vicohome_last_event` | Sensor | Details of the latest event (timestamp, traceId, imageUrl, videoUrl) |
| `sensor.vicohome_battery` | Sensor | Battery level (%) |
| `sensor.vicohome_signal` | Sensor | Wi-Fi signal strength (dBm) |
| `sensor.vicohome_ip` | Sensor | Device IP address |
| `sensor.vicohome_firmware` | Sensor | Firmware version |
| `binary_sensor.vicohome_bewegung` | Binary Sensor | Motion detected (triggers on new event) |
| `binary_sensor.vicohome_online` | Binary Sensor | Device online/offline status |
| `binary_sensor.vicohome_event_type` | Binary Sensor | Event type indicator |
| `camera.vicohome_camera` | Camera | Snapshot from the last event |
| `image.vicohome_last_event` | Image | Latest event image (downloadable) |
| `button.vicohome_snapshot` | Button | Trigger manual snapshot |
| `button.vicohome_refresh` | Button | Force event refresh |
| `button.vicohome_restart` | Button | Restart device |
| `switch.vicohome_benachrichtigungen` | Switch | Telegram notifications ON/OFF |
| `number.vicohome_aktualisierungsintervall` | Number | Polling interval (s) |
| `text.vicohome_telegram_bot_token` | Text | Bot token (password mode) |
| `text.vicohome_telegram_empfanger_id` | Text | Chat/recipient ID |

### How It Works

1. The coordinator periodically logs in to `api-{region}.vicohome.io` and fetches recent events.
2. The device serial number is **persistently cached** — survives Home Assistant restarts.
3. If a **new event** (new `traceId`) is found, the binary sensor flips to `on`.
4. If notifications are enabled, it sends a Telegram message with:
   - Formatted text (device name, time, trace ID)
   - Inline photo (snapshot)
   - MP4 video (transcoded from M3U8 via ffmpeg, max 50 MB)
5. All temporary files in `/tmp/` are cleaned up immediately after upload.

### Known Limitations

- **No live stream** — VicoHome cloud API does not expose a public RTSP/HTTP live stream. Only event-based snapshots and video clips.
- **M3U8 video expiry** — Video URLs from the cloud API expire after a short window. Very old events may not have a downloadable video.
- **Single-session VicoHome token** — Parallel logins may kick the integration out. The integration auto-reconnects, but a brief gap in polling can occur.
- **Cloud-only** — Works only while the camera is online and connected to VicoHome servers.

### Troubleshooting

| Issue | Fix |
|---|---|
| "cannot connect" during setup | Check e-mail/password and region (EU vs US). |
| Camera shows *Unavailable* | No motion events in the last hour — trigger motion or wait. |
| No Telegram video received | Video might exceed 50 MB or URL expired. Lower resolution in VicoHome app or reduce polling interval. |
| ffmpeg timeout | Ensure `/tmp` has enough space. For large M3U8 playlists, video may exceed 120 s transcoding. |
| Entities not loading after restart | Wait for the next polling cycle — the serial cache ensures fast recovery. |

### Security & Privacy

| Concern | Status |
|---|---|
| Hardcoded credentials | ❌ **None** — everything is user-configured via HA UI |
| Token storage | ✅ In Home Assistant's encrypted `.storage` |
| Network calls | 🔒 HTTPS only to `api-{region}.vicohome.io` |
| Temporary video cache | 🗑️ Immediately deleted from `/tmp` after Telegram upload |

> ⚠️ **Do not share your Home Assistant `.storage` backups publicly** — they may contain your device credentials and Telegram bot token.

### Changelog

**v1.3.0**
- 🌍 Full English + German localization for all entities
- 📝 New `translations/en.json` and `translations/de.json`
- 🔧 All entity names now use Home Assistant translation system (`translation_key` + `has_entity_name`)
- 📨 Notification messages default to English
- ⚠️ Breaking: Entity IDs now use English names by default

**v1.2.0** (2026-05-03)
- 🔧 Fix: Persistent serial cache — no more "Blocking IO" warnings on restart
- 🎛️ New: Button platform (snapshot, refresh, restart)
- 🖼️ New: Image entity for latest event photo
- 📊 Enhanced sensors: battery, signal, IP, firmware, online status
- 💾 Device details survive HA restarts via local cache

**v1.1.1**
- Initial stable release with motion detection, camera snapshot, and Telegram notifications

### License

MIT © 2026 TomTje
