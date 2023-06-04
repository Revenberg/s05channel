"""s0 channel."""
import logging
import threading
from collections import OrderedDict
from typing import Any, Dict, Optional

from homeassistant.core import HomeAssistant

from .const import DOMAIN
import serial

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

class ConnectionException(Exception):
    """Base class for other exceptions."""

    pass

class S05ChannelException(Exception):
    """Base class for other exceptions."""

    pass


class HubInitFailed(S05ChannelException):
    """Raised when an error happens during init."""

    pass


class DeviceInitFailed(S05ChannelException):
    """Raised when a device can't be initialized."""

    pass

class s05channelReadError(S05ChannelException):
    """Raised when a s05channel read fails."""

    pass


class s05channelWriteError(S05ChannelException):
    """Raised when a s05channel write fails."""

    pass


class DataUpdateFailed(S05ChannelException):
    """Raised when an update cycle fails."""

    pass


class DeviceInvalid(S05ChannelException):
    """Raised when a device is not usable or invalid."""

    pass


class S05ChannelMultiHub:
    """S05ChannelMultiHub."""
    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        device: str,
    ):
        """Initialize the s05channel hub."""
        self._hass = hass
        self._name = name
        self._device = device
        self._lock = threading.Lock()
        self._id = name.lower()
        self._coordinator_timeout = 30
        self._client = None
        self._id = name.lower()
        self._lock = threading.Lock()
        self.inverters = []
        self.meters = []

        self.initalized = False
        self._online = False

    async def _async_init_s05channel(self) -> None:
        """Async_init_s05channel."""
        
        inverter_unit_id = 1

        try:
            new_inverter = S05ChannelInverter(inverter_unit_id, self)
            await self._hass.async_add_executor_job(new_inverter.init_device)
            self.inverters.append(new_inverter)

        except s05channelReadError as e:
            _LOGGER.debug("---------------1---------------------------")
            raise HubInitFailed(f"{e}")

        except DeviceInvalid as e:
            """Inverters are required"""
            _LOGGER.error(f"Inverter device ID {inverter_unit_id}: {e}")
            raise HubInitFailed(f"{e}")

        try:
            for inverter in self.inverters:
                await self._hass.async_add_executor_job(inverter.read_s05channel_data)

        except s05channelReadError as e:
            self._online = False
            raise HubInitFailed(f"Read error: {e}")

        except DeviceInvalid as e:
            self._online = False
            raise HubInitFailed(f"Invalid device: {e}")

        except ConnectionException as e:
            self._online = False
            raise HubInitFailed(f"Connection failed: {e}")

        self.initalized = True

    async def async_refresh_s05channel_data(self, _now: Optional[int] = None) -> bool:
        """async_refresh_s05channel_data."""
        if not self.is_socket_open():
            await self.connect()

        if not self.initalized:
            try:
                await self._async_init_s05channel()

            except ConnectionException as e:
                raise HubInitFailed(f"Setup failed: {e}")

        self._online = True
        try:
            for inverter in self.inverters:
                await self._hass.async_add_executor_job(inverter.read_s05channel_data)

        except s05channelReadError as e:
            self._online = False
            raise DataUpdateFailed(f"Update failed: {e}")

        except DeviceInvalid as e:
            self._online = False
            raise DataUpdateFailed(f"Invalid device: {e}")

        except ConnectionException as e:
            self._online = False
            raise DataUpdateFailed(f"Connection failed: {e}")

        return True

    @property
    def online(self):
        return self._online

    @property
    def name(self):
        """Return the name of this hub."""
        return self._name

    @property
    def hub_id(self) -> str:
        return self._id

    @property
    def coordinator_timeout(self) -> int:
        _LOGGER.debug(f"coordinator timeout is {self._coordinator_timeout}")
        return self._coordinator_timeout

    async def connect(self) -> None:
        """Connect s05channel client."""
        if self._client is None:
            BAUDRATE = 9600
            self._client = serial.Serial(
                  self._device,
                  BAUDRATE,
                  timeout=10,
                  bytesize=serial.SEVENBITS,
                  parity=serial.PARITY_EVEN,
                  stopbits=serial.STOPBITS_ONE
            )

    def is_socket_open(self) -> bool:
        """Check s05channel client connection status."""
        if self._client is None:
            return False

        return True

    async def shutdown(self) -> None:
        """Shut down the hub."""
        self._online = False
        self._client = None

class S05ChannelInverter:
    _delta_energy = 0
    def __init__(self, device_id: int, hub: S05ChannelMultiHub) -> None:
        """Init."""
        
        self.inverter_unit_id = device_id
        self.hub = hub
        self.decoded_common = []
        self.decoded_model = []
        self.has_parent = False
        self.global_power_control = None
        self.manufacturer = "S05Channel"
        self._delta_energy = 0

    def init_device(self) -> None:
        """init_device."""
        
        _LOGGER.debug("init_device")
        self.read_s05channel_data_common()

        #self.manufacturer = self.decoded_common["C_Manufacturer"]
        self.manufacturer = "S05Channel"
        #self.model = self.decoded_common["C_Model"]
        self.model = "S05 Channel"
        #self.option = self.decoded_common["C_Option"]
        #self.fw_version = self.decoded_common["C_Version"]

        self.fw_version = self.decoded_common["C_SunSpec_DID"]
        #self.serial = self.decoded_common["C_SerialNumber"]
        self.serial = self.decoded_common["SN"]
        self.device_address = f"{self.hub._host}"

        #self.name = f"{self.hub.hub_id.capitalize()} I{self.inverter_unit_id}"
        self.uid_base = f"{self.hub.hub_id.capitalize()} I"
        + self.decoded_common["C_SunSpec_DID"]

        self._device_info = {
            "identifiers": {(DOMAIN, int(self.decoded_common["C_SunSpec_DID"]))},
            "name": self.device_address,
            "manufacturer": "S05Channel",
            "model": self.model,
            "sw_version": self.fw_version,
            #"hw_version": self.option,
        }

    def round(self, floatval):
        return round(floatval, 2)

    def read_s05channel_data_common(self) -> None:
        #_LOGGER.debug("read_s05channel_data")

        try:
            self.hub.connect()
        except ConnectionException as e:
            _LOGGER.error(f"Connection error: {e}")
            self._online = False
            raise s05channelReadError(f"{e}")


    def read_s05channel_data(self) -> None:
        # _LOGGER.debug("read_s05channel_data")

        try:
              line = self._instrument.readline()
        except Exception as e:
              _LOGGER.error(f'exception: {e}')
              #print(traceback.format_exc())
            #_LOGGER.debug("==================== line =========================================")
        _LOGGER.info(line)
        #_LOGGER.debug("=============================================================")
        _LOGGER.info(line.decode("utf-8") )
        values = line.decode("utf-8").split(":")
        _LOGGER.info(values[1])
        _LOGGER.info(values[6])
        _LOGGER.info(values[9])
        _LOGGER.info(values[12])
        _LOGGER.info(values[15])
        _LOGGER.info(values[18])
        _LOGGER.info( values )

        self.decoded_model = OrderedDict(
            [
                ("p", values[1]),
                ("p1", values[6]),
                ("p2", values[9]),
                ("p3", values[11]),
                ("p4", values[15]),
                ("p5", values[18]),
            ]
        )

        self.hub._online = True
        _LOGGER.debug(f"Inverter: {self.decoded_model}")

    @property
    def online(self) -> bool:
        """Device is online."""
        return self.hub.online

    @property
    def device_info(self) -> Optional[Dict[str, Any]]:
        return self._device_info
