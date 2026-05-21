"""Binary sensor platform for VicoHome."""

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo, DeviceEntryType

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
    """Set up VicoHome binary sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        VicoHomeMotionSensor(coordinator),
        VicoHomeOnlineSensor(coordinator),
        VicoHomeChargingSensor(coordinator),
        VicoHomeAwakeSensor(coordinator),
        VicoHomeRecordingAudioSensor(coordinator),
        VicoHomeLiveAudioSensor(coordinator),
        VicoHomeAlarmRemoveSensor(coordinator),
        VicoHomeOtaAwakeSensor(coordinator),
        VicoHomeActivatedSensor(coordinator),
        VicoHomeDormancyPlanSensor(coordinator),
        VicoHomeSdCardSensor(coordinator),
        VicoHomeFirmwareStatusSensor(coordinator),
    ]
    async_add_entities(entities)


class VicoHomeMotionSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor that turns on when a new event is detected."""

    _attr_has_entity_name = True
    _attr_translation_key = "motion"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_motion"
        self._attr_device_class = BinarySensorDeviceClass.MOTION
        self._attr_device_info = _device_info(coordinator)
        self._last_triggered = None
        self._last_event_count = 0

    @property
    def is_on(self) -> bool:
        events = self.coordinator.data.get("events", [])
        count = len(events)
        if count > 0 and count != self._last_event_count:
            self._last_event_count = count
            self._last_triggered = self.coordinator.data.get("last_update")
            return True
        return False

    @property
    def extra_state_attributes(self):
        return {
            "last_triggered": self._last_triggered,
            "event_count_in_window": self.coordinator.data.get("event_count", 0),
        }


class VicoHomeOnlineSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor showing if camera is online."""

    _attr_has_entity_name = True
    _attr_translation_key = "online"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_online"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_device_info = _device_info(coordinator)

    @property
    def is_on(self) -> bool:
        dd = self.coordinator.data.get("device_details", {})
        return dd.get("online") == 1

    @property
    def available(self) -> bool:
        return "online" in self.coordinator.data.get("device_details", {})


class VicoHomeChargingSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor showing if camera is charging."""

    _attr_has_entity_name = True
    _attr_translation_key = "charging"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_charging"
        self._attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING
        self._attr_device_info = _device_info(coordinator)

    @property
    def is_on(self) -> bool:
        dd = self.coordinator.data.get("device_details", {})
        return dd.get("isCharging") == 1

    @property
    def available(self) -> bool:
        return "isCharging" in self.coordinator.data.get("device_details", {})


class VicoHomeAwakeSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor showing if camera is awake (not sleeping)."""

    _attr_has_entity_name = True
    _attr_translation_key = "awake"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_awake"
        self._attr_device_info = _device_info(coordinator)

    @property
    def is_on(self) -> bool:
        dd = self.coordinator.data.get("device_details", {})
        return dd.get("awake") == 1

    @property
    def available(self) -> bool:
        return "awake" in self.coordinator.data.get("device_details", {})

    @property
    def extra_state_attributes(self):
        dd = self.coordinator.data.get("device_details", {})
        wake_ts = dd.get("deviceDormancyWakeTime")
        return {
            "dormancy_plan_switch": dd.get("dormancyPlanSwitch"),
            "wake_time": wake_ts,
        }


class VicoHomeRecordingAudioSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor showing if recording audio is enabled."""

    _attr_has_entity_name = True
    _attr_translation_key = "recording_audio"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_recording_audio"
        self._attr_device_info = _device_info(coordinator)

    @property
    def is_on(self) -> bool:
        dd = self.coordinator.data.get("device_details", {})
        return dd.get("recordingAudioToggleOn") is True

    @property
    def available(self) -> bool:
        return "recordingAudioToggleOn" in self.coordinator.data.get("device_details", {})


class VicoHomeLiveAudioSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor showing if live audio is enabled."""

    _attr_has_entity_name = True
    _attr_translation_key = "live_audio"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_live_audio"
        self._attr_device_info = _device_info(coordinator)

    @property
    def is_on(self) -> bool:
        dd = self.coordinator.data.get("device_details", {})
        return dd.get("liveAudioToggleOn") is True

    @property
    def available(self) -> bool:
        return "liveAudioToggleOn" in self.coordinator.data.get("device_details", {})


class VicoHomeAlarmRemoveSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for alarm when camera is removed."""

    _attr_has_entity_name = True
    _attr_translation_key = "alarm_remove"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_alarm_remove"
        self._attr_device_info = _device_info(coordinator)

    @property
    def is_on(self) -> bool:
        dd = self.coordinator.data.get("device_details", {})
        return dd.get("alarmWhenRemoveToggleOn") is True

    @property
    def available(self) -> bool:
        return "alarmWhenRemoveToggleOn" in self.coordinator.data.get("device_details", {})


class VicoHomeOtaAwakeSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor showing if OTA update happens on awake."""

    _attr_has_entity_name = True
    _attr_translation_key = "ota_awake"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_ota_awake"
        self._attr_device_info = _device_info(coordinator)

    @property
    def is_on(self) -> bool:
        dd = self.coordinator.data.get("device_details", {})
        return dd.get("otaOnAwake") is True

    @property
    def available(self) -> bool:
        return "otaOnAwake" in self.coordinator.data.get("device_details", {})


class VicoHomeActivatedSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor showing if device is activated."""

    _attr_has_entity_name = True
    _attr_translation_key = "activated"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_activated"
        self._attr_device_info = _device_info(coordinator)

    @property
    def is_on(self) -> bool:
        dd = self.coordinator.data.get("device_details", {})
        return dd.get("activated") == 1

    @property
    def available(self) -> bool:
        return "activated" in self.coordinator.data.get("device_details", {})


class VicoHomeDormancyPlanSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor showing if dormancy plan is active."""

    _attr_has_entity_name = True
    _attr_translation_key = "dormancy_plan"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_dormancy_plan"
        self._attr_device_info = _device_info(coordinator)

    @property
    def is_on(self) -> bool:
        dd = self.coordinator.data.get("device_details", {})
        return dd.get("dormancyPlanSwitch") == 1

    @property
    def available(self) -> bool:
        return "dormancyPlanSwitch" in self.coordinator.data.get("device_details", {})


class VicoHomeSdCardSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor showing if SD card is present."""

    _attr_has_entity_name = True
    _attr_translation_key = "sd_card"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_sd_card"
        self._attr_device_class = BinarySensorDeviceClass.PRESENCE
        self._attr_device_info = _device_info(coordinator)

    @property
    def is_on(self) -> bool:
        dd = self.coordinator.data.get("device_details", {})
        sd = dd.get("sdCard", {})
        return sd.get("total", 0) > 0

    @property
    def available(self) -> bool:
        return "sdCard" in self.coordinator.data.get("device_details", {})

    @property
    def extra_state_attributes(self):
        dd = self.coordinator.data.get("device_details", {})
        sd = dd.get("sdCard", {})
        return {
            "total_mb": sd.get("total"),
            "used_mb": sd.get("used"),
            "free_mb": sd.get("free"),
            "format_status": sd.get("formatStatus"),
        }


class VicoHomeFirmwareStatusSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor showing if firmware is up to date."""

    _attr_has_entity_name = True
    _attr_translation_key = "firmware_current"


    def __init__(self, coordinator: VicoHomeCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.email}_firmware_current"
        self._attr_device_info = _device_info(coordinator)

    @property
    def is_on(self) -> bool:
        dd = self.coordinator.data.get("device_details", {})
        return dd.get("firmwareStatus") == 0

    @property
    def available(self) -> bool:
        return "firmwareStatus" in self.coordinator.data.get("device_details", {})

    @property
    def extra_state_attributes(self):
        dd = self.coordinator.data.get("device_details", {})
        return {
            "current": dd.get("firmwareId"),
            "newest": dd.get("newestFirmwareId"),
        }
