"""DataUpdateCoordinator for VicoHome."""

import aiohttp
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN, DEFAULT_POLLING_INTERVAL,
    CONF_EMAIL, CONF_PASSWORD, CONF_REGION, CONF_POLLING_INTERVAL,
    CONF_NOTIFICATIONS, CONF_TELEGRAM_BOT, CONF_TELEGRAM_CHAT,
)

_LOGGER = logging.getLogger(__name__)


async def _async_load_cached_serial(hass: HomeAssistant) -> str | None:
    """Load cached serial number from persistent storage (async-safe)."""
    path = Path(hass.config.config_dir) / ".storage" / "vicohome_serial.json"
    if not path.exists():
        return None
    try:
        data = await hass.async_add_executor_job(lambda: json.loads(path.read_text()))
        return data.get("serial")
    except Exception:
        return None


async def _async_save_cached_serial(hass: HomeAssistant, serial: str) -> None:
    """Save serial number to persistent storage (async-safe)."""
    path = Path(hass.config.config_dir) / ".storage" / "vicohome_serial.json"
    try:
        await hass.async_add_executor_job(lambda: path.write_text(json.dumps({"serial": serial})))
    except Exception as err:
        _LOGGER.debug("Could not save cached serial: %s", err)


class VicoHomeCoordinator(DataUpdateCoordinator):
    """VicoHome data coordinator."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.entry = entry
        self.email = entry.data[CONF_EMAIL]
        self.password = entry.data[CONF_PASSWORD]
        self.region = entry.data.get(CONF_REGION, "eu")
        self.interval = entry.data.get(CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL)

        # Runtime-editable options
        opts = entry.options or {}
        self.notifications_enabled = opts.get(CONF_NOTIFICATIONS, False)
        self.telegram_bot_token = opts.get(CONF_TELEGRAM_BOT, "")
        self.telegram_chat_id = opts.get(CONF_TELEGRAM_CHAT, "")

        self.base_url = f"https://api-{self.region}.vicohome.io"
        self._token: str | None = None
        self._last_notified_trace_id: str | None = None
        self._cached_serial: str | None = None  # Will be loaded async in first update

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=self.interval),
        )

    async def _async_update_data(self):
        """Fetch events and device details from VicoHome API."""
        if not self._token:
            await self._async_login()
        
        # Load cached serial on first run (async-safe)
        if self._cached_serial is None:
            self._cached_serial = await _async_load_cached_serial(self.hass)
            if self._cached_serial:
                _LOGGER.debug("Loaded cached serial from storage: %s", self._cached_serial)

        try:
            events = await self._async_fetch_events()
        except UpdateFailed as err:
            msg = str(err).lower()
            # If kicked or token invalid, force re-login and retry once
            if "kicked" in msg or "token" in msg or "auth" in msg:
                _LOGGER.debug("Token invalidated (%s), forcing re-login and retry", err)
                self._token = None
                await self._async_login()
                events = await self._async_fetch_events()
            else:
                raise

        now = datetime.now(timezone.utc)

        # Extract serial number from events and persist it
        serial = None
        if events:
            serial = events[0].get("serialNumber")
            if serial and serial != self._cached_serial:
                self._cached_serial = serial
                await _async_save_cached_serial(self.hass, serial)
                _LOGGER.debug("Cached new serial from events: %s", serial)
        
        # Fallback to cached serial if no events and we have one stored
        if not serial:
            serial = self._cached_serial
            if serial:
                _LOGGER.debug("Using cached serial (no recent events): %s", serial)
        
        # Fetch device details if we have a serial
        device_details = {}
        if serial:
            device_details = await self._async_fetch_device_details(serial)

        # Send Telegram notification for new events
        if events and self.notifications_enabled and self.telegram_bot_token and self.telegram_chat_id:
            latest = events[0]
            trace_id = latest.get("traceId")
            if trace_id and trace_id != self._last_notified_trace_id:
                self._last_notified_trace_id = trace_id
                await self._async_send_telegram(latest)

        return {
            "events": events,
            "last_update": now,
            "event_count": len(events),
            "device_details": device_details,
            "serial_number": serial,
        }

    async def _async_login(self) -> None:
        """Login and get token."""
        payload = {
            "email": self.email,
            "password": self.password,
            "loginType": 0,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/account/login",
                json=payload,
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                data = await resp.json()
                if data.get("result") != 0:
                    raise UpdateFailed(f"Login failed: {data.get('msg', 'unknown error')}")
                self._token = data["data"]["token"]["token"]

    async def _async_fetch_events(self) -> list:
        """Fetch recent events."""
        now = datetime.now(timezone.utc)
        start = now - timedelta(hours=1)
        payload = {
            "startTimestamp": str(int(start.timestamp())),
            "endTimestamp": str(int(now.timestamp())),
            "language": "de",
            "countryNo": "DE" if self.region == "eu" else "US",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/library/newselectlibrary",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": self._token,
                },
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                data = await resp.json()
                if data.get("result") != 0:
                    self._token = None
                    raise UpdateFailed(f"Event fetch failed: {data.get('msg')}")
                return data.get("data", {}).get("list", [])

    async def _async_fetch_device_details(self, serial: str) -> dict:
        """Fetch device details by serial number."""
        _LOGGER.debug("Fetching device details for serial: %s", serial)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/device/selectsingledevice",
                json={"serialNumber": serial},
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": self._token,
                },
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                data = await resp.json()
                _LOGGER.debug("Device details raw response: %s", data)
                if data.get("result") != 0:
                    _LOGGER.warning("Device details fetch failed: %s", data.get('msg'))
                    return {}
                dd = data.get("data", {})
                _LOGGER.debug("Device details keys: %s", list(dd.keys()) if isinstance(dd, dict) else "not dict")
                return dd

    async def _async_send_telegram(self, event: dict) -> None:
        """Send Telegram notification for a new event."""
        device_name = event.get("deviceName", "unknown")
        ts_raw = event.get("timestamp")
        try:
            from datetime import datetime, timezone
            ts_int = int(ts_raw)
            ts_dt = datetime.fromtimestamp(ts_int, tz=timezone.utc).astimezone()
            ts_str = ts_dt.strftime("%d.%m.%Y, %H:%M:%S")
        except Exception:
            ts_str = str(ts_raw)

        trace_id = event.get("traceId", "n/a")
        image_url = event.get("imageUrl", "")
        video_url = event.get("videoUrl", "")

        msg = (
            f"🎥 *VicoHome Motion detected!*\n\n"
            f"📷 Device: {device_name}\n"
            f"⏰ Time: {ts_str}\n"
            f"🆔 Trace: `{trace_id}`"
        )

        await self._async_send_telegram_text(msg)

        # Send image directly as photo if available
        if image_url:
            await self._async_send_telegram_photo(image_url, f"VicoHome – {device_name}")

        # Send video as upload (download to memory + post as FormData) – no disk cache
        if video_url:
            await self._async_send_telegram_video(video_url, f"VicoHome – {device_name}")

    async def _async_send_telegram_text(self, text: str) -> None:
        """Send text message via Telegram Bot API."""
        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    result = await resp.json()
                    if not result.get("ok"):
                        _LOGGER.error("Telegram text error: %s", result.get("description"))
        except Exception as err:
            _LOGGER.error("Telegram text failed: %s", err)

    async def _async_send_telegram_photo(self, photo_url: str, caption: str) -> None:
        """Send photo directly via Telegram Bot API."""
        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendPhoto"
        payload = {
            "chat_id": self.telegram_chat_id,
            "photo": photo_url,
            "caption": caption,
            "parse_mode": "Markdown",
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    result = await resp.json()
                    if not result.get("ok"):
                        _LOGGER.warning("Telegram photo error: %s", result.get("description"))
        except Exception as err:
            _LOGGER.error("Telegram photo failed: %s", err)

    async def _async_send_telegram_video(self, m3u8_url: str, caption: str) -> None:
        """Download M3U8 stream, convert to MP4 via ffmpeg, upload Telegram sendVideo, then clean up."""
        from pathlib import Path
        import asyncio
        import uuid

        tmp_path = Path(f"/tmp/vicohome_{uuid.uuid4().hex[:8]}.mp4")

        try:
            # 1) ffmpeg: M3U8 → MP4
            proc = await asyncio.create_subprocess_exec(
                "ffmpeg", "-y", "-fflags", "+discardcorrupt",
                "-i", m3u8_url,
                "-c", "copy",
                "-movflags", "+faststart",
                str(tmp_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)

            if proc.returncode != 0:
                err = stderr.decode("utf-8", "replace")[-400:]
                _LOGGER.warning("ffmpeg failed (rc=%s): %s", proc.returncode, err)
                return

            if not tmp_path.exists() or tmp_path.stat().st_size == 0:
                _LOGGER.warning("ffmpeg produced empty MP4")
                return

            # Check Telegram 50MB limit
            size_mb = tmp_path.stat().st_size / (1024 * 1024)
            if size_mb > 50:
                _LOGGER.warning("Video %.1fMB >50MB limit, skipping sendVideo", size_mb)
                return

            # 2) Upload MP4 to Telegram
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendVideo"
            from aiohttp import FormData
            form = FormData()
            form.add_field("chat_id", self.telegram_chat_id)
            from pathlib import Path
            with open(tmp_path, "rb") as f:
                form.add_field(
                    "video",
                    f,
                    filename="vicohome_motion.mp4",
                    content_type="video/mp4",
                )
                form.add_field("caption", caption)
                form.add_field("supports_streaming", "true")

                async with aiohttp.ClientSession() as session:
                    async with session.post(url, data=form, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                        result = await resp.json()
                        if not result.get("ok"):
                            _LOGGER.warning("Telegram video error: %s", result.get("description"))

        except asyncio.TimeoutError:
            _LOGGER.error("ffmpeg or Telegram upload timed out")
        except Exception as err:
            _LOGGER.error("Telegram video failed: %s", err)

        finally:
            # 3) Clean up temp file
            if tmp_path.exists():
                tmp_path.unlink()

    async def _async_send_telegram_document(self, doc_bytes: bytes, ext: str, caption: str) -> None:
        """Fallback: send as document upload."""
        try:
            import io
            from aiohttp import FormData
            form = FormData()
            form.add_field("chat_id", self.telegram_chat_id)
            form.add_field(
                "document",
                io.BytesIO(doc_bytes),
                filename=f"vicohome_motion{ext}",
            )
            form.add_field("caption", caption)
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendDocument"
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=form, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    result = await resp.json()
                    if not result.get("ok"):
                        _LOGGER.warning("Telegram sendDocument fallback error: %s", result.get("description"))
        except Exception as err:
            _LOGGER.error("Telegram document fallback failed: %s", err)

    # --- Runtime setters (persist in config entry options) ---

    async def async_set_notifications(self, enabled: bool) -> None:
        """Enable/disable notifications."""
        self.notifications_enabled = enabled
        opts = {**(self.entry.options or {}), CONF_NOTIFICATIONS: enabled}
        self.hass.config_entries.async_update_entry(self.entry, options=opts)
        await self.async_request_refresh()

    async def async_set_interval(self, seconds: int) -> None:
        """Set polling interval."""
        self.interval = seconds
        self.update_interval = timedelta(seconds=seconds)
        opts = {**(self.entry.options or {}), CONF_POLLING_INTERVAL: seconds}
        self.hass.config_entries.async_update_entry(self.entry, options=opts)
        await self.async_request_refresh()

    async def async_set_telegram_bot(self, token: str) -> None:
        """Set Telegram bot token."""
        self.telegram_bot_token = token
        opts = {**(self.entry.options or {}), CONF_TELEGRAM_BOT: token}
        self.hass.config_entries.async_update_entry(self.entry, options=opts)
        await self.async_request_refresh()

    async def async_set_telegram_chat(self, chat_id: str) -> None:
        """Set Telegram chat ID."""
        self.telegram_chat_id = chat_id
        opts = {**(self.entry.options or {}), CONF_TELEGRAM_CHAT: chat_id}
        self.hass.config_entries.async_update_entry(self.entry, options=opts)
        await self.async_request_refresh()
