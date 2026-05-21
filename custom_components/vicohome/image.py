"""Image platform for VicoHome."""

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo, DeviceEntryType

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
    """Set up VicoHome image entity."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([VicoHomeImage(coordinator)])


class VicoHomeImage(CoordinatorEntity, ImageEntity):
    """Image entity showing the latest event snapshot directly in HA."""

    _attr_has_entity_name = True
    _attr_translation_key = "last_image"

    def __init__(self, coordinator: VicoHomeCoordinator):
        CoordinatorEntity.__init__(self, coordinator)
        ImageEntity.__init__(self, coordinator.hass)
        self._attr_unique_id = f"{coordinator.email}_image"
        self._attr_device_info = _device_info(coordinator)
        self._attr_content_type = "image/jpeg"

    @property
    def available(self):
        events = self.coordinator.data.get("events", [])
        if not events:
            return False
        return bool(events[0].get("imageUrl"))

    @property
    def image_url(self):
        """Return direct URL for HA to display."""
        events = self.coordinator.data.get("events", [])
        if not events:
            return None
        return events[0].get("imageUrl")

    async def async_image(self):
        """Fetch latest event snapshot."""
        import aiohttp
        url = self.image_url
        if not url:
            return None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    return await resp.read()
        except Exception:
            return None
