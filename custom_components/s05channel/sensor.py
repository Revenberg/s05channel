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

    _LOGGER.debug("async_setup_entry 1")
    hub = hass.data[DOMAIN][config_entry.entry_id]["hub"]
    _LOGGER.debug("async_setup_entry 2")
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    _LOGGER.debug("async_setup_entry 3 coordinator" )
    _LOGGER.debug(coordinator)

    entities = []

    _LOGGER.debug("?!??!??!??!??!??!?")
    _LOGGER.debug(hub._nr)
    _LOGGER.debug(hub.inverters)
    for inverter in hub.inverters:

        _LOGGER.debug("entities 0")
        _LOGGER.debug(inverter.device_id)

        _LOGGER.debug("entities 1")
        entities.append(S05ChannelDevice(inverter, config_entry, coordinator))
        _LOGGER.debug("entities 2")
        entities.append(S05ChannelSN(inverter, config_entry, coordinator))
        _LOGGER.debug("entities 2b")
        entities.append(S05ChannelDeviceId(inverter, config_entry, coordinator))
        _LOGGER.debug("entities 3")
        entities.append(S05ChannelPath(inverter, config_entry, coordinator))
        _LOGGER.debug("entities 4")
        entities.append(S05ChannelStatus(inverter, config_entry, coordinator))
        _LOGGER.debug("entities 5")
        #entities.append(StatusVendor(inverter, config_entry, coordinator))
        _LOGGER.debug("entities 6")
        entities.append(S05ChannelPort(inverter, config_entry, coordinator, "1"))
        _LOGGER.debug("entities 7")
        entities.append(S05ChannelPort(inverter, config_entry, coordinator, "2"))
        _LOGGER.debug("entities 8")
        entities.append(S05ChannelPort(inverter, config_entry, coordinator, "3"))
        _LOGGER.debug("entities 9")
        entities.append(S05ChannelPort(inverter, config_entry, coordinator, "4"))
        _LOGGER.debug("entities 10")
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

    _LOGGER.debug("S05ChannelDevice")
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

        return f"Device {self._platform.hub.name}"

    @property
    def native_value(self):
        """native_value."""

        return f"{self._platform.model}"

    @property
    def extra_state_attributes(self):
        """extra_state_attributes."""

        attrs = {}

        _LOGGER.debug("native_value ...2...")
        attrs["device_id"] = self._platform.device_id
        attrs["manufacturer"] = self._platform.manufacturer
        attrs["device_address"] = self._platform.device_address
        attrs["model"] = self._platform.model

        if self._platform.has_parent:
            attrs["parent_device_id"] = self._platform.inverter_unit_id

        attrs["serial_number"] = self._platform.serial

        return attrs

class S05ChannelSN(S05ChannelSensorBase):
    """S05ChannelSN."""

    entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, platform, config_entry, coordinator):
        """Initialize the sensor."""
        super().__init__(platform, config_entry, coordinator)

    @property
    def unique_id(self) -> str:
        """unique_id."""

        return f"{self._platform.uid_base}_S05ChannelSN"

    @property
    def name(self) -> str:
        """Name."""

        return f"Serial number {self._platform.hub.name}"

    @property
    def native_value(self):
        """native_value."""

        return self._platform.decoded_common["SN"]

class S05ChannelDeviceId(S05ChannelSensorBase):
    """S05Channel device id."""

    entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, platform, config_entry, coordinator):
        """Initialize the sensor."""
        super().__init__(platform, config_entry, coordinator)

    @property
    def unique_id(self) -> str:
        """unique_id."""

        return f"{self._platform.uid_base}_S05ChannelDeviceId"

    @property
    def name(self) -> str:
        """Name."""

        _LOGGER.debug("native_value ...1?1...")
        _LOGGER.debug("self._platform.hub.name")
        _LOGGER.debug(self._platform.decoded_common)
        return f"Device id {self._platform.hub.name}"

    @property
    def native_value(self):
        """native_value."""

        _LOGGER.debug("native_value ...2?2...")
        _LOGGER.debug(self._platform.decoded_common)
        _LOGGER.debug(self._platform.decoded_common["device_id"])
        return self._platform.decoded_common["device_id"]

class S05ChannelPath(S05ChannelSensorBase):
    """S05ChannelPath."""

    entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, platform, config_entry, coordinator):
        """Initialize the sensor."""
        super().__init__(platform, config_entry, coordinator)

    @property
    def unique_id(self) -> str:
        """unique_id."""

        return f"{self._platform.uid_base}_S05ChannelPath"

    @property
    def name(self) -> str:
        """Name."""

        return f"Channel Path {self._platform.hub.name}"

    @property
    def native_value(self):
        """native_value."""

        _LOGGER.debug("native_value ...1...")
        _LOGGER.debug(self._platform.decoded_common)

        return self._platform.decoded_common["device_address"]

class S05ChannelPort(S05ChannelSensorBase):
    """S05ChannelPort."""

    device_class = SensorDeviceClass.ENERGY
    state_class = SensorStateClass.TOTAL_INCREASING
#    state_class = SensorStateClass.MEASUREMENT
    native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

    suggested_display_precision = 0

    def __init__(self, platform, config_entry, coordinator, port: str = None):
        """Initialize the sensor."""

        super().__init__(platform, config_entry, coordinator)
        _LOGGER.debug("__init__")
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
            return f"{self._platform.hub.name}"
        else:
            return f"{self._platform.hub.name} Port {self._port.upper()}"

    @property
    def native_value(self):
        """native_value."""

        if self._port is None:
            model_key = "p"
        else:
            model_key = f"p{self._port}"

        _LOGGER.debug("native_value")
        _LOGGER.debug(model_key)
        _LOGGER.debug(self._platform.decoded_model["status"])

        if self._platform.decoded_model["status"] == "Running":
            return self._platform.decoded_model[model_key]
        else:
            return None

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

        return f"Status {self._platform.hub.name}"

    @property
    def native_value(self):
        """native_value."""

        return self._platform.decoded_model["status"]

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
