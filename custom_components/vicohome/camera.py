"""Camera platform for VicoHome."""

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo, DeviceEntryType
import aiohttp

from .const import DOMAIN
from .coordinator import VicoHomeCoordinator


def _device_info(coordinator: VicoHomeCoordinator):
    return DeviceInfo(
        identifiers={(DOMAIN, coordinator.email)},
        name=f"VicoHome ({coordinator.email})",
        manufacturer="VicoHome",
        model="Cloud Camera",
        entry_type=DeviceEntryType.SERVICE,
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up VicoHome camera."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([VicoHomeCamera(coordinator)])


class VicoHomeCamera(CoordinatorEntity, Camera):
    """Camera entity showing the latest event snapshot."""

    _attr_has_entity_name = True
    _attr_translation_key = "camera"

    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        Camera.__init__(self)
        self._webrtc_provider = None
        self._attr_unique_id = f"{coordinator.email}_camera"
        self._attr_is_streaming = False
        self._attr_is_recording = False
        self._attr_device_info = _device_info(coordinator)

    @property
    def available(self):
        return self.coordinator.last_update_success

    async def async_camera_image(self, width=None, height=None):
        """Return camera image."""
        events = self.coordinator.data.get("events", [])
        if not events:
            return None
        image_url = events[0].get("imageUrl")
        if not image_url:
            return None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    return await resp.read()
        except Exception:
            return None

    @property
    def extra_state_attributes(self):
        events = self.coordinator.data.get("events", [])
        if not events:
            return {}
        ev = events[0]
        return {
            "trace_id": ev.get("traceId"),
            "timestamp": ev.get("timestamp"),
            "video_url": ev.get("videoUrl"),
        }
