"""Switch platform for VicoHome."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo, DeviceEntryType

from .const import DOMAIN
from .coordinator import VicoHomeCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up VicoHome switches."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([VicoHomeNotificationsSwitch(coordinator)])


class VicoHomeNotificationsSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to enable/disable VicoHome notifications."""

    _attr_has_entity_name = True
    _attr_translation_key = "notifications"

    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_notifications"
        self._attr_icon = "mdi:bell"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.email)},
            name=f"VicoHome ({coordinator.email})",
            manufacturer="VicoHome",
            model="Cloud Camera",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def is_on(self) -> bool:
        return self.coordinator.notifications_enabled

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_notifications(True)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_notifications(False)
