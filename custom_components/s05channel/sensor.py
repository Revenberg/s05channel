"""Sensor."""

import logging
#import re

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
#    PERCENTAGE,
#    POWER_VOLT_AMPERE_REACTIVE,
#    UnitOfApparentPower,
#    UnitOfElectricCurrent,
#    UnitOfElectricPotential,
    UnitOfEnergy,
#    UnitOfFrequency,
#    UnitOfPower,
#    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    #BATTERY_STATUS,
    #BATTERY_STATUS_TEXT,
#    DEVICE_STATUS,
    DEVICE_STATUS_TEXT,
    #VENDOR_STATUS,
    DOMAIN,
#    ENERGY_VOLT_AMPERE_HOUR,
#    ENERGY_VOLT_AMPERE_REACTIVE_HOUR,
    #METER_EVENTS,
#    MMPPT_EVENTS,
#    RRCR_STATUS,
#    SUNSPEC_DID,
#    SUNSPEC_SF_RANGE,
#    VENDOR_STATUS,
#    BatteryLimit,
#    SunSpecAccum,
    #SunSpecNotImpl,
)
#from .helpers import  update_accum
# scale_factor, float_to_hex
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """async_setup_entry."""

    hub = hass.data[DOMAIN][config_entry.entry_id]["hub"]
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    entities = []

    for inverter in hub.inverters:
        entities.append(S05ChannelDevice(inverter, config_entry, coordinator))
#        entities.append(Version(inverter, config_entry, coordinator))
        entities.append(S05ChannelStatus(inverter, config_entry, coordinator))
        #entities.append(StatusVendor(inverter, config_entry, coordinator))
        entities.append(S05ChannelPort(inverter, config_entry, coordinator))
        entities.append(S05ChannelPort(inverter, config_entry, coordinator, "1"))
        entities.append(S05ChannelPort(inverter, config_entry, coordinator, "2"))
        entities.append(S05ChannelPort(inverter, config_entry, coordinator, "3"))
        entities.append(S05ChannelPort(inverter, config_entry, coordinator, "4"))
        entities.append(S05ChannelPort(inverter, config_entry, coordinator, "5"))

    _LOGGER.debug(entities)
    if entities:
        async_add_entities(entities)

class S05ChannelSensorBase(CoordinatorEntity, SensorEntity):
    """S05ChannelSensorBase."""

    should_poll = False
    #suggested_display_precision = 3
    _attr_has_entity_name = True

    def __init__(self, platform, config_entry, coordinator):
        """Pass coordinator to CoordinatorEntity."""

        super().__init__(coordinator)
        """Initialize the sensor."""
        self._platform = platform
        self._config_entry = config_entry

    @property
    def device_info(self):
        """device_info."""

        return self._platform.device_info

    @property
    def config_entry_id(self):
        """config_entry_id."""

        return self._config_entry.entry_id

    @property
    def config_entry_name(self):
        """config_entry_name."""

        return self._config_entry.data["name"]

    @property
    def available(self) -> bool:
        """available."""

        return self._platform.online

    @callback
    def _handle_coordinator_update(self) -> None:
        """_handle_coordinator_update."""

        self.async_write_ha_state()

class S05ChannelDevice(S05ChannelSensorBase):
    """S05ChannelDevice."""

    entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, platform, config_entry, coordinator):
        """Initialize the sensor."""

        super().__init__(platform, config_entry, coordinator)

    @property
    def unique_id(self) -> str:
        """unique_id."""

        return f"{self._platform.uid_base}_device"

    @property
    def name(self) -> str:
        """Name."""

        return "Device"

    @property
    def native_value(self):
        """native_value."""

        return self._platform.model

    @property
    def extra_state_attributes(self):
        """extra_state_attributes."""

        attrs = {}

        attrs["device_id"] = self._platform.device_address
        attrs["manufacturer"] = self._platform.manufacturer
        attrs["model"] = self._platform.model

        if self._platform.has_parent:
            attrs["parent_device_id"] = self._platform.inverter_unit_id

        attrs["serial_number"] = self._platform.serial

        return attrs


#class Version(S05ChannelSensorBase):
#    """Version."""

#    entity_category = EntityCategory.DIAGNOSTIC

#    def __init__(self, platform, config_entry, coordinator):
#        """Initialize the sensor."""
#        super().__init__(platform, config_entry, coordinator)

#    @property
#    def unique_id(self) -> str:
#        """unique_id."""

#        return f"{self._platform.uid_base}_version"

#    @property
#    def name(self) -> str:
#        """Name."""

#        return "Version"

#    @property
#    def native_value(self):
#        """native_value."""

#        return self._platform.fw_version

class S05ChannelPort(S05ChannelSensorBase):
    """S05ChannelPort."""

    device_class = SensorDeviceClass.ENERGY
    state_class = SensorStateClass.TOTAL_INCREASING
    native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    suggested_display_precision = 0

    def __init__(self, platform, config_entry, coordinator, port: str = None):
        """Initialize the sensor."""

        super().__init__(platform, config_entry, coordinator)
        self._port = port

    @property
    def unique_id(self) -> str:
        """unique_id."""

        if self._port is None:
            return f"{self._platform.uid_base}_s05channel_port"
        else:
            return f"{self._platform.uid_base}_s05channel_port_p{self._port.lower()}"

    @property
    def name(self) -> str:
        """name."""

        if self._port is None:
            return "S05Channel"
        else:
            return f"S05Channel Port {self._port.upper()}"

    @property
    def native_value(self):
        """native_value."""

        if self._port is None:
            model_key = "p"
        else:
            model_key = f"p{self._port}"

        _LOGGER.debug("native_value")
        _LOGGER.debug(model_key)

        return self._platform.decoded_model[model_key]

class S05ChannelStatusSensor(S05ChannelSensorBase):
    """S05ChannelStatusSensor."""

    device_class = SensorDeviceClass.ENUM
    entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, platform, config_entry, coordinator):
        """Initialize the sensor."""

        super().__init__(platform, config_entry, coordinator)

    @property
    def unique_id(self) -> str:
        """unique_id."""

        return f"{self._platform.uid_base}_status"

    @property
    def name(self) -> str:
        """Name."""

        return "Status"

    @property
    def native_value(self):
        """native_value."""

        return "Active"

class S05ChannelStatus(S05ChannelStatusSensor):
    """S05ChannelStatus."""

    options = list(DEVICE_STATUS_TEXT.values())

    def __init__(self, platform, config_entry, coordinator):
        """Initialize the sensor."""

        super().__init__(platform, config_entry, coordinator)

    @property
    def unique_id(self) -> str:
        """unique_id."""

        return f"{self._platform.uid_base}_i_status"

    @property
    def native_value(self):
        """native_value."""

        _LOGGER.debug(" native_value i_status")
        return self._platform.decoded_model["status"]

    @property
    def extra_state_attributes(self):
        """extra_state_attributes."""

        attrs = {}
        _LOGGER.debug(" extra_state_attributes")

#        try:
#            if self._platform.decoded_model["i_status"] in DEVICE_STATUS:
#                _LOGGER.debug("1")
#                attrs["status_text"] = DEVICE_STATUS_TEXT[
#                    self._platform.decoded_model["i_status"]
#                ]
#                attrs["status_value"] = self._platform.decoded_model["i_status"]
#            _LOGGER.debug("2")
#        except KeyError:
#            pass

        _LOGGER.debug(attrs)
        return attrs

#class StatusVendor(S05ChannelSensorBase):
#    """StatusVendor."""

#    device_class = SensorDeviceClass.ENUM
#    entity_category = EntityCategory.DIAGNOSTIC
#    options = list(DEVICE_STATUS_TEXT.values())

#    def __init__(self, platform, config_entry, coordinator):
#        """Initialize the sensor."""

#        super().__init__(platform, config_entry, coordinator)

#    @property
#    def unique_id(self) -> str:
#        """unique_id."""

#        return f"{self._platform.uid_base}_status_vendor"

#    @property
#    def name(self) -> str:
#        """NAme."""

#        return "Status Vendor"

#    @property
#    def native_value(self):
#        """native_value."""

#        _LOGGER.debug("i_status_vendor")
#        _LOGGER.debug(self._platform.decoded_model["i_status_vendor"])
#        _LOGGER.debug(DEVICE_STATUS_TEXT[self._platform.decoded_model["i_status_vendor"]])

#        return DEVICE_STATUS_TEXT[self._platform.decoded_model["i_status_vendor"]]
#        return "Running"

#    @property
#    def extra_state_attributes(self):
#        """extra_state_attributes."""

#        attrs = {}
#        _LOGGER.debug("i_status_vendor extra_state_attributes")

#        try:
#            if self._platform.decoded_model["i_status_vendor"] in DEVICE_STATUS_TEXT:
#                _LOGGER.debug("3")
#                attrs["status_text"] = DEVICE_STATUS_TEXT[
#                    self._platform.decoded_model["i_status_vendor"]
#                ]
#                attrs["status_value"] = self._platform.decoded_model["i_status_vendor"]

#        except KeyError:
#            pass
#        _LOGGER.debug(attrs)
#        return attrs
