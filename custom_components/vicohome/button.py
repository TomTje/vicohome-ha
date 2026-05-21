"""Button platform for VicoHome."""

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo, DeviceEntryType

from .const import DOMAIN
from .coordinator import VicoHomeCoordinator


def _device_info(coordinator: VicoHomeCoordinator) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, coordinator.email)},
        name=f"VicoHome ({coordinator.email})",
        manufacturer="VicoHome",
        model="Cloud Camera",
        entry_type=DeviceEntryType.SERVICE,
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up VicoHome buttons."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([VicoHomeVideoButton(coordinator)])


class VicoHomeVideoButton(CoordinatorEntity, ButtonEntity):
    """Button that opens the latest event video URL via persistent notification."""

    _attr_has_entity_name = True
    _attr_translation_key = "open_video"

    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_video_btn"
        self._attr_device_info = _device_info(coordinator)
        self._attr_icon = "mdi:video"

    async def async_press(self) -> None:
        """Send a HA notification with clickable video and image links."""
        events = self.coordinator.data.get("events", [])
        hass = self.hass
        if not events:
            hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "VicoHome Video",
                    "message": "No events available.",
                    "notification_id": "vicohome_no_event",
                },
            )
            return

        ev = events[0]
        video_url = ev.get("videoUrl", "")
        image_url = ev.get("imageUrl", "")
        device_name = ev.get("deviceName", "Smart-Camera")
        trace_id = ev.get("traceId", "n/a")

        if not video_url:
            hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": f"VicoHome – {device_name}",
                    "message": f"No video available for event {trace_id}.",
                    "notification_id": f"vicohome_{trace_id}",
                },
            )
            return

        msg = (
            f"🎥 [Open Video]({video_url})\n\n"
            f"📷 [View Image]({image_url})\n"
            f"🆔 Trace: `{trace_id}`"
        )

        hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": f"VicoHome – {device_name}",
                "message": msg,
                "notification_id": f"vicohome_{trace_id}",
            },
        )
