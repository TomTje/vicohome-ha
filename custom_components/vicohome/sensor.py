"""Sensor platform for VicoHome."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo, DeviceEntryType
from datetime import datetime, timezone

from .const import DOMAIN
from .coordinator import VicoHomeCoordinator


def _device_info(coordinator: VicoHomeCoordinator) -> DeviceInfo:
    dd = coordinator.data.get("device_details", {})
    return DeviceInfo(
        identifiers={(DOMAIN, coordinator.email)},
        name=dd.get("deviceName", f"VicoHome ({coordinator.email})"),
        manufacturer="VicoHome",
        model=dd.get("displayModelNo", "Cloud Camera"),
        sw_version=dd.get("firmwareId"),
        entry_type=DeviceEntryType.SERVICE,
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up VicoHome sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        VicoHomeEventCountSensor(coordinator),
        VicoHomeLastEventSensor(coordinator),
        VicoHomeBatterySensor(coordinator),
        VicoHomeSignalSensor(coordinator),
        VicoHomeFirmwareSensor(coordinator),
        VicoHomeResolutionSensor(coordinator),
        VicoHomeIpSensor(coordinator),
        VicoHomeWakeTimeSensor(coordinator),
        VicoHomeStatusTextSensor(coordinator),
        VicoHomeWifiModeSensor(coordinator),
        VicoHomeLocationSensor(coordinator),
        VicoHomeMacSensor(coordinator),
        VicoHomeModelSensor(coordinator),
        VicoHomeHomeNameSensor(coordinator),
        VicoHomeActivationSensor(coordinator),
        VicoHomeDeviceStatusSensor(coordinator),
        VicoHomeWhiteLightSensor(coordinator),
        VicoHomeWifiChannelSensor(coordinator),
        VicoHomeMcuSensor(coordinator),
        VicoHomeRoleSensor(coordinator),
        VicoHomeTimezoneSensor(coordinator),
    ]
    async_add_entities(entities)


class VicoHomeEventCountSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing number of events in last hour."""

    _attr_has_entity_name = True
    _attr_translation_key = "event_count"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_event_count"
        self._attr_native_unit_of_measurement = "events"
        self._attr_device_info = _device_info(coordinator)

    @property
    def native_value(self):
        return self.coordinator.data.get("event_count", 0)

    @property
    def extra_state_attributes(self):
        return {
            "last_update": self.coordinator.data.get("last_update"),
        }


class VicoHomeLastEventSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing details of the last/most recent event."""

    _attr_has_entity_name = True
    _attr_translation_key = "last_event"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_last_event"
        self._attr_device_info = _device_info(coordinator)

    @property
    def available(self) -> bool:
        events = self.coordinator.data.get("events", [])
        return len(events) > 0

    @property
    def native_value(self):
        events = self.coordinator.data.get("events", [])
        if not events:
            return None
        return events[0].get("deviceName", "unknown")

    @property
    def extra_state_attributes(self):
        events = self.coordinator.data.get("events", [])
        if not events:
            return {}
        ev = events[0]
        return {
            "trace_id": ev.get("traceId"),
            "timestamp": ev.get("timestamp"),
            "period_seconds": ev.get("period"),
            "file_size": ev.get("fileSize"),
            "ai_tags": ev.get("deviceAiEventList", []),
            "image_url": ev.get("imageUrl"),
            "video_url": ev.get("videoUrl"),
            "event_count": len(events),
        }


class VicoHomeBatterySensor(CoordinatorEntity, SensorEntity):
    """Sensor showing battery level."""

    _attr_has_entity_name = True
    _attr_translation_key = "battery"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_battery"
        self._attr_native_unit_of_measurement = "%"
        self._attr_device_class = "battery"
        self._attr_device_info = _device_info(coordinator)

    @property
    def native_value(self):
        dd = self.coordinator.data.get("device_details", {})
        return dd.get("batteryLevel")

    @property
    def available(self) -> bool:
        return "batteryLevel" in self.coordinator.data.get("device_details", {})


class VicoHomeSignalSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing WiFi signal strength."""

    _attr_has_entity_name = True
    _attr_translation_key = "signal"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_signal"
        self._attr_native_unit_of_measurement = "dBm"
        self._attr_device_class = "signal_strength"
        self._attr_device_info = _device_info(coordinator)

    @property
    def native_value(self):
        dd = self.coordinator.data.get("device_details", {})
        return dd.get("signalStrength")

    @property
    def available(self) -> bool:
        return "signalStrength" in self.coordinator.data.get("device_details", {})


class VicoHomeFirmwareSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing firmware version."""

    _attr_has_entity_name = True
    _attr_translation_key = "firmware"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_firmware"
        self._attr_device_info = _device_info(coordinator)

    @property
    def native_value(self):
        dd = self.coordinator.data.get("device_details", {})
        return dd.get("firmwareId")

    @property
    def available(self) -> bool:
        return "firmwareId" in self.coordinator.data.get("device_details", {})


class VicoHomeResolutionSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing recording resolution."""

    _attr_has_entity_name = True
    _attr_translation_key = "resolution"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_resolution"
        self._attr_device_info = _device_info(coordinator)

    @property
    def native_value(self):
        dd = self.coordinator.data.get("device_details", {})
        return dd.get("recResolution")

    @property
    def available(self) -> bool:
        return "recResolution" in self.coordinator.data.get("device_details", {})


class VicoHomeIpSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing camera IP address."""

    _attr_has_entity_name = True
    _attr_translation_key = "ip"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_ip"
        self._attr_device_info = _device_info(coordinator)

    @property
    def native_value(self):
        dd = self.coordinator.data.get("device_details", {})
        return dd.get("ip")

    @property
    def available(self) -> bool:
        return "ip" in self.coordinator.data.get("device_details", {})


class VicoHomeWakeTimeSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing when camera will wake from sleep."""

    _attr_has_entity_name = True
    _attr_translation_key = "wake_time"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_wake_time"
        self._attr_device_class = "timestamp"
        self._attr_device_info = _device_info(coordinator)

    @property
    def native_value(self):
        dd = self.coordinator.data.get("device_details", {})
        wake_ts = dd.get("deviceDormancyWakeTime")
        if wake_ts:
            return datetime.fromtimestamp(wake_ts, tz=timezone.utc)
        return None

    @property
    def available(self) -> bool:
        return "deviceDormancyWakeTime" in self.coordinator.data.get("device_details", {})


class VicoHomeStatusTextSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing device status text (e.g. sleeping message)."""

    _attr_has_entity_name = True
    _attr_translation_key = "status_text"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_status_text"
        self._attr_device_info = _device_info(coordinator)

    @property
    def native_value(self):
        dd = self.coordinator.data.get("device_details", {})
        return dd.get("deviceDormancyMessage")

    @property
    def available(self) -> bool:
        return "deviceDormancyMessage" in self.coordinator.data.get("device_details", {})


class VicoHomeWifiModeSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing WiFi power mode."""

    _attr_has_entity_name = True
    _attr_translation_key = "wifi_mode"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_wifi_mode"
        self._attr_device_info = _device_info(coordinator)

    @property
    def native_value(self):
        dd = self.coordinator.data.get("device_details", {})
        modes = {0: "default", 1: "turbo"}
        val = dd.get("wifiPowerLevel")
        return modes.get(val, val)

    @property
    def available(self) -> bool:
        return "wifiPowerLevel" in self.coordinator.data.get("device_details", {})


class VicoHomeLocationSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing camera location name."""

    _attr_has_entity_name = True
    _attr_translation_key = "location"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_location"
        self._attr_device_info = _device_info(coordinator)

    @property
    def native_value(self):
        dd = self.coordinator.data.get("device_details", {})
        return dd.get("locationName")

    @property
    def available(self) -> bool:
        return "locationName" in self.coordinator.data.get("device_details", {})


class VicoHomeMacSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing MAC address."""

    _attr_has_entity_name = True
    _attr_translation_key = "mac"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_mac"
        self._attr_device_info = _device_info(coordinator)

    @property
    def native_value(self):
        dd = self.coordinator.data.get("device_details", {})
        return dd.get("macAddress")

    @property
    def available(self) -> bool:
        return "macAddress" in self.coordinator.data.get("device_details", {})


class VicoHomeModelSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing device model number."""

    _attr_has_entity_name = True
    _attr_translation_key = "model"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_model"
        self._attr_device_info = _device_info(coordinator)

    @property
    def native_value(self):
        dd = self.coordinator.data.get("device_details", {})
        return dd.get("modelNo")

    @property
    def available(self) -> bool:
        return "modelNo" in self.coordinator.data.get("device_details", {})


class VicoHomeHomeNameSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing home name."""

    _attr_has_entity_name = True
    _attr_translation_key = "home_name"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_home_name"
        self._attr_device_info = _device_info(coordinator)

    @property
    def native_value(self):
        dd = self.coordinator.data.get("device_details", {})
        return dd.get("homeName")

    @property
    def available(self) -> bool:
        return "homeName" in self.coordinator.data.get("device_details", {})


class VicoHomeActivationSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing activation timestamp."""

    _attr_has_entity_name = True
    _attr_translation_key = "activation"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_activated"
        self._attr_device_class = "timestamp"
        self._attr_device_info = _device_info(coordinator)

    @property
    def native_value(self):
        dd = self.coordinator.data.get("device_details", {})
        ts = dd.get("activatedTime")
        if ts:
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        return None

    @property
    def available(self) -> bool:
        return "activatedTime" in self.coordinator.data.get("device_details", {})


class VicoHomeDeviceStatusSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing numeric device status."""

    _attr_has_entity_name = True
    _attr_translation_key = "device_status"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_device_status"
        self._attr_device_info = _device_info(coordinator)

    @property
    def native_value(self):
        dd = self.coordinator.data.get("device_details", {})
        return dd.get("deviceStatus")

    @property
    def available(self) -> bool:
        return "deviceStatus" in self.coordinator.data.get("device_details", {})


class VicoHomeWhiteLightSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing white light level."""

    _attr_has_entity_name = True
    _attr_translation_key = "white_light"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_white_light"
        self._attr_device_info = _device_info(coordinator)

    @property
    def native_value(self):
        dd = self.coordinator.data.get("device_details", {})
        return dd.get("whiteLight")

    @property
    def available(self) -> bool:
        return "whiteLight" in self.coordinator.data.get("device_details", {})


class VicoHomeWifiChannelSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing WiFi channel."""

    _attr_has_entity_name = True
    _attr_translation_key = "wifi_channel"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_wifi_channel"
        self._attr_device_info = _device_info(coordinator)

    @property
    def native_value(self):
        dd = self.coordinator.data.get("device_details", {})
        return dd.get("wifiChannel")

    @property
    def available(self) -> bool:
        return "wifiChannel" in self.coordinator.data.get("device_details", {})


class VicoHomeMcuSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing MCU firmware version."""

    _attr_has_entity_name = True
    _attr_translation_key = "mcu"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_mcu"
        self._attr_device_info = _device_info(coordinator)

    @property
    def native_value(self):
        dd = self.coordinator.data.get("device_details", {})
        return dd.get("mcuNumber")

    @property
    def available(self) -> bool:
        return "mcuNumber" in self.coordinator.data.get("device_details", {})


class VicoHomeRoleSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing user role."""

    _attr_has_entity_name = True
    _attr_translation_key = "role"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_role"
        self._attr_device_info = _device_info(coordinator)

    @property
    def native_value(self):
        dd = self.coordinator.data.get("device_details", {})
        return dd.get("roleName")

    @property
    def available(self) -> bool:
        return "roleName" in self.coordinator.data.get("device_details", {})


class VicoHomeTimezoneSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing timezone."""

    _attr_has_entity_name = True
    _attr_translation_key = "timezone"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_timezone"
        self._attr_device_info = _device_info(coordinator)

    @property
    def native_value(self):
        dd = self.coordinator.data.get("device_details", {})
        return dd.get("timeZone")

    @property
    def available(self) -> bool:
        return "timeZone" in self.coordinator.data.get("device_details", {})
