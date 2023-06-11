"""s0 channel."""
import logging
import threading
from collections import OrderedDict
from typing import Any, Optional
# Dict

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

    count = 0

    @classmethod
    def incr(self) -> int:
        """Increment of class counter."""
        self.count += 1
        return self.count

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        device: str,
    ):
        """Initialize the s05channel hub."""
        _LOGGER.debug("S05ChannelMultiHub")
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
        """Async init s05channel."""

        _LOGGER.debug("_async_init_s05channel 1")
        inverter_unit_id = self.incr()

        try:
            _LOGGER.debug("_async_init_s05channel 2")
            new_inverter = S05ChannelInverter(inverter_unit_id, self)
            _LOGGER.debug("_async_init_s05channel 3")
            await self._hass.async_add_executor_job(new_inverter.init_device)
            _LOGGER.debug("_async_init_s05channel 4")
            self.inverters.append(new_inverter)
            _LOGGER.debug("_async_init_s05channel 5")

        except s05channelReadError as e:
            _LOGGER.debug("---------------1- 2 - -------------------------")
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

        _LOGGER.debug("async_refresh_s05channel_data")
        self.connect()

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
        """Omline."""

        return self._online

    @property
    def name(self):
        """Return the name of this hub."""
        return self._name

    @property
    def hub_id(self) -> str:
        """Return id."""
        return self._id

    @property
    def coordinator_timeout(self) -> int:
        """coordinator_timeout."""
        _LOGGER.debug(f"coordinator timeout is {self._coordinator_timeout}")
        return self._coordinator_timeout

    def connect(self) -> None:
        """Connect s05channel client."""
        _LOGGER.debug("connect 1")
        _LOGGER.debug(self._device)
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

    @property
    def readline(self) -> str:
        """Readline."""

        _LOGGER.debug("readline 1")
        _LOGGER.debug(self._client)

        if self._client is None:
            self.connect()

        _LOGGER.debug("readline 2")
        line = self._client.readline()
        _LOGGER.debug(line)
        _LOGGER.debug("readline 3")
        line = line.decode("utf-8")
        _LOGGER.debug("readline 4")
        return line

#    def is_socket_open(self) -> bool:
#        """Check s05channel client connection status."""

#        _LOGGER.debug("is_socket_open")
#        if self._client is None:
#            return False

#        return True

    async def shutdown(self) -> None:
        """Shut down the hub."""
        self._online = False
        self._client = None

class S05ChannelInverter:
    """S05ChannelInverter."""

#    _delta_energy = 0
    def __init__(self, device_id: int, hub: S05ChannelMultiHub) -> None:
        """Init."""

        _LOGGER.debug("S05ChannelInverter")
        self.device_id = device_id
        self.hub = hub
        self.decoded_common = []
        self.decoded_model = []
        self.has_parent = False
        self.global_power_control = None
        self.manufacturer = "S05Channel"
 #       self._delta_energy = 0

    def init_device(self) -> None:
        """init_device."""

        _LOGGER.debug("init_device")
        self.read_s05channel_data_common()

        self.manufacturer = "S05Channel"
        self.model = "S05 Channel"

        _LOGGER.debug("------------------11----------------------------------------------------")
        _LOGGER.debug(self.decoded_common)
        self.serial = self.decoded_common["SN"]
        _LOGGER.debug("------------------22----------------------------------------------------")
        self.device_address = f"{self.hub._device}"
        _LOGGER.debug("------------------33----------------------------------------------------")

        h = self.hub._device.replace("/", "_")
        self.uid_base = f"{self.hub.hub_id.capitalize()} I{h}"
        _LOGGER.debug(self.hub._device)
        _LOGGER.debug(self.uid_base)

        self._device_info = {
            "identifiers": {(DOMAIN, int(self.decoded_common["SN"]))},
            "name": self.device_address,
            "sn": self.decoded_common["SN"],
            "device_address": self.device_address,
            "device_id": self.device_id,
            "manufacturer": "S05Channel",
            "model": self.model,
        }

    def read_s05channel_data_common(self) -> None:
        """Set common."""

        _LOGGER.debug("==================== read_s05channel_data_common =========================================")

        try:
            _LOGGER.debug("==================== read =========================================")
            line = self.hub.readline
            _LOGGER.info(line)
            _LOGGER.debug("==================== common =========================================")
            values = line.split(":")
            _LOGGER.info(values[1])
            _LOGGER.info(self.hub._device)

            self.decoded_common = OrderedDict(
                [
                    ("SN", values[1]),
                    ("device_id", self.device_id),
                    ("device_address", self.hub._device),
                ]
            )
        except Exception as e:
            _LOGGER.debug("==================== common Exception 1=========================================")
            _LOGGER.error(f'exception: {e}')

    def read_s05channel_data(self) -> None:
        """Read data."""
        _LOGGER.debug("read_s05channel_data 0")

        try:
            _LOGGER.debug("===================== read_s05channel_data 1 ========================================")
            line = self.hub.readline
            _LOGGER.debug("===================== read_s05channel_data 2 ========================================")
            _LOGGER.info(line)

            if (line != ""):
                _LOGGER.debug("===================== read_s05channel_data 3 ========================================")
                _LOGGER.info(line)
                values = line.split(":")
                _LOGGER.debug("===================== read_s05channel_data 5 ========================================")
                _LOGGER.info(values[1])
                _LOGGER.info(values[6])
                _LOGGER.info(values[9])
                _LOGGER.info(values[12])
                _LOGGER.info(values[15])
                _LOGGER.info(values[18])
                _LOGGER.info( values )

                self.decoded_model = OrderedDict(
                    [
                        ("status", "Running"),
                        ("SN", values[1]),
                        ("p1", values[6]),
                        ("p2", values[9]),
                        ("p3", values[11]),
                        ("p4", values[15]),
                        ("p5", values[18]),
#                        ("device_address", F"overbodig {self.device_address}"),
                    ]
                )

                self.hub._online = True
                _LOGGER.debug(f"Inverter: {self.decoded_model}")
            else:
                self.hub._online = False
                self.decoded_model = OrderedDict(
                    [
                        ("status", "Stopped"),
                    ]
                )

        except Exception as e:
            _LOGGER.debug("==================== line Exception =========================================")
            _LOGGER.error(f'exception: {e}')
            self.decoded_model = OrderedDict(
                [
                    ("status", "Stopped"),
                ]
            )
              #print(traceback.format_exc())
            #_LOGGER.debug("==================== line =========================================")

    @property
    def online(self) -> bool:
        """Device is online."""

        return self.hub.online

    @property
    def device_info(self) -> Optional[dict[str, Any]]:
        """device_info."""

        return self._device_info
