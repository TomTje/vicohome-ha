"""Number platform for VicoHome."""

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo, DeviceEntryType

from .const import DOMAIN
from .coordinator import VicoHomeCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up VicoHome number entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([VicoHomePollingInterval(coordinator)])


class VicoHomePollingInterval(CoordinatorEntity, NumberEntity):
    """Number entity to adjust polling interval."""

    _attr_native_min_value = 60
    _attr_native_max_value = 3600
    _attr_native_step = 30
    _attr_native_unit_of_measurement = "s"

    _attr_has_entity_name = True
    _attr_translation_key = "polling_interval"

    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_polling_interval"
        self._attr_icon = "mdi:timer"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.email)},
            name=f"VicoHome ({coordinator.email})",
            manufacturer="VicoHome",
            model="Cloud Camera",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> float | None:
        return float(self.coordinator.interval)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_interval(int(value))
