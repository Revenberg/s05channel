"""The s05channel Integration."""
import asyncio
import logging
from datetime import timedelta
from typing import Any
import glob

import async_timeout
import serial
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    Platform,
)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN,  ConfDefaultInt
# ConfDefaultFlag,
from .const import RetrySettings
#ConfName,
from .hub import DataUpdateFailed, HubInitFailed, S05ChannelMultiHub

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

PLATFORMS: list[str] = [
    Platform.SENSOR,
]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up an S0 meter."""

    _LOGGER.debug( "!!!!!!!! async_setup_entry !!!!!!!!!!!!!!" )
    _LOGGER.debug(  entry.data )

    entry_updates: dict[str, Any] = {}
    if CONF_SCAN_INTERVAL in entry.data:
        data = {**entry.data}
        entry_updates["data"] = data
        entry_updates["options"] = {
            **entry.options,
            CONF_SCAN_INTERVAL: data.pop(CONF_SCAN_INTERVAL),
        }
    if entry_updates:
        hass.config_entries.async_update_entry(entry, **entry_updates)

    ports = glob.glob('/dev/ttyACM[0-9]*')
    _LOGGER.debug(  ports )

    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()

            _LOGGER.debug( port )
            _LOGGER.debug( entry.data[CONF_HOST] )
            if port == entry.data[CONF_HOST]:
                s05channel_hub = S05ChannelMultiHub(
                    hass,
                    entry.data[CONF_NAME],
                    entry.data[CONF_HOST]
                )

                coordinator = S05ChannelCoordinator(
                    hass,
                    s05channel_hub,
                    entry.options.get(CONF_SCAN_INTERVAL, ConfDefaultInt.SCAN_INTERVAL),
                )

                _LOGGER.debug("...................................")
                _LOGGER.debug(entry.entry_id)
                hass.data.setdefault(DOMAIN, {})
                hass.data[DOMAIN][entry.entry_id] = {
                    "hub": s05channel_hub,
                    "coordinator": coordinator,
                }

                await coordinator.async_config_entry_first_refresh()

                await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

                entry.async_on_unload(entry.add_update_listener(async_reload_entry))

        except Exception:
            pass

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    s05channel_hub = hass.data[DOMAIN][entry.entry_id]["hub"]
    await s05channel_hub.shutdown()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle an options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Remove a config entry from a device."""
    s05channel_hub = hass.data[DOMAIN][config_entry.entry_id]["hub"]

    known_devices = []

    for inverter in s05channel_hub.inverters:
        inverter_device_ids = {
            dev_id[1]
            for dev_id in inverter.device_info["identifiers"]
            if dev_id[0] == DOMAIN
        }
        for dev_id in inverter_device_ids:
            known_devices.append(dev_id)

    for meter in s05channel_hub.meters:
        meter_device_ids = {
            dev_id[1]
            for dev_id in meter.device_info["identifiers"]
            if dev_id[0] == DOMAIN
        }
        for dev_id in meter_device_ids:
            known_devices.append(dev_id)

    this_device_ids = {
        dev_id[1] for dev_id in device_entry.identifiers if dev_id[0] == DOMAIN
    }

    for device_id in this_device_ids:
        if device_id in known_devices:
            _LOGGER.error(f"Failed to remove device entry: device {device_id} in use")
            return False

    return True


class S05ChannelCoordinator(DataUpdateCoordinator):
    """S05ChannelCoordinator."""

    def __init__(
        self, hass: HomeAssistant, hub: S05ChannelMultiHub, scan_interval: int
    ):
        """Init so channel coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="S05Channel Coordinator",
            update_interval=timedelta(seconds=scan_interval),
        )
        self._hub = hub

    async def _async_update_data(self):
        try:
            async with async_timeout.timeout(self._hub.coordinator_timeout):
                return await self._refresh_s05channel_data_with_retry(
                    ex_type=DataUpdateFailed,
                    limit=RetrySettings.Limit,
                    wait_ms=RetrySettings.Time,
                    wait_ratio=RetrySettings.Ratio,
                )

        except HubInitFailed as e:
            raise UpdateFailed(f"{e}")

        except DataUpdateFailed as e:
            raise UpdateFailed(f"{e}")

    async def _refresh_s05channel_data_with_retry(
        self,
        ex_type=Exception,
        limit=0,
        wait_ms=100,
        wait_ratio=2,
    ):
        """Retry refresh until no exception occurs or retries exhaust."""

        _LOGGER.debug("_refresh_s05channel_data_with_retry")
        attempt = 1
        while True:
            try:
                #return await self._hub.async_refresh_s05channel_data()
                return await self._hub.async_refresh_s05channel_data()
            except Exception as ex:
                if not isinstance(ex, ex_type):
                    raise ex
                if 0 < limit <= attempt:
                    _LOGGER.debug(f"No more data refresh attempts (maximum {limit})")
                    raise ex

                _LOGGER.debug(f"Failed data refresh attempt #{attempt}", exc_info=ex)

                attempt += 1
                _LOGGER.debug(
                    f"Waiting {wait_ms} ms before data refresh attempt #{attempt}"
                )
                await asyncio.sleep(wait_ms / 1000)
                wait_ms *= wait_ratio
