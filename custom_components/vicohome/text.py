"""Text platform for VicoHome."""

from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo, DeviceEntryType

from .const import DOMAIN
from .coordinator import VicoHomeCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up VicoHome text entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        VicoHomeTelegramBot(coordinator),
        VicoHomeTelegramChat(coordinator),
    ])


class VicoHomeTelegramBot(CoordinatorEntity, TextEntity):
    """Text entity for Telegram bot token."""

    _attr_has_entity_name = True
    _attr_translation_key = "telegram_bot"

    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_telegram_bot"
        self._attr_icon = "mdi:robot"
        self._attr_mode = "password"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.email)},
            name=f"VicoHome ({coordinator.email})",
            manufacturer="VicoHome",
            model="Cloud Camera",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> str | None:
        token = self.coordinator.telegram_bot_token
        return token if token else None

    async def async_set_value(self, value: str) -> None:
        await self.coordinator.async_set_telegram_bot(value)


class VicoHomeTelegramChat(CoordinatorEntity, TextEntity):
    """Text entity for Telegram chat/recipient ID."""

    _attr_has_entity_name = True
    _attr_translation_key = "telegram_chat"

    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_telegram_chat"
        self._attr_icon = "mdi:send"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.email)},
            name=f"VicoHome ({coordinator.email})",
            manufacturer="VicoHome",
            model="Cloud Camera",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> str | None:
        chat = self.coordinator.telegram_chat_id
        return chat if chat else None

    async def async_set_value(self, value: str) -> None:
        await self.coordinator.async_set_telegram_chat(value)
