"""Config flow."""
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from .const import DEFAULT_NAME, DOMAIN, ConfDefaultInt

@callback
def s05channel_multi_entries(hass: HomeAssistant):
    """Return the hosts already configured."""
    return {
        entry.data[CONF_HOST] for entry in hass.config_entries.async_entries(DOMAIN)
    }

class S05ChannelMultiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """S05Channel configflow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        """async_get_options_flow."""
        
        return S05ChannelMultiOptionsFlowHandler(config_entry)

    def _host_in_configuration_exists(self, host) -> bool:
        """Return True if host exists in configuration."""
        if host in s05channel_multi_entries(self.hass):
            return True
        return False

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            if self._host_in_configuration_exists(user_input[CONF_HOST]):
                errors[CONF_HOST] = "already_configured"
            else:
                await self.async_set_unique_id(user_input[CONF_HOST])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )
        else:
            user_input = {
                CONF_NAME: DEFAULT_NAME,
                CONF_HOST: "",
                CONF_PORT: ConfDefaultInt.PORT,
#                ConfName.NUMBER_INVERTERS: ConfDefaultInt.NUMBER_INVERTERS,
#                ConfName.DEVICE_ID: ConfDefaultInt.DEVICE_ID,
            }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_NAME, default=user_input[CONF_NAME]): cv.string,
                    vol.Required(CONF_HOST, default=user_input[CONF_HOST]): cv.string,
                    vol.Required(CONF_PORT, default=user_input[CONF_PORT]): vol.Coerce(
                        int
                    ),
 #                   vol.Required(
 #                       f"{ConfName.NUMBER_INVERTERS}",
 #                       default=user_input[ConfName.NUMBER_INVERTERS],
 #                   ): vol.Coerce(int),
 #                   vol.Required(
 #                       f"{ConfName.DEVICE_ID}", default=user_input[ConfName.DEVICE_ID]
 #                   ): vol.Coerce(int),
                },
            ),
            errors=errors,
        )


class S05ChannelMultiOptionsFlowHandler(config_entries.OptionsFlow):
    """S05ChannelMultiOptionsFlowHandler."""
    
    def __init__(self, config_entry: ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        """async_step_init."""
        
        errors = {}

        """Manage the options."""
        if user_input is not None:
            if user_input[CONF_SCAN_INTERVAL] < 1:
                errors[CONF_SCAN_INTERVAL] = "invalid_scan_interval"
            elif user_input[CONF_SCAN_INTERVAL] > 86400:
                errors[CONF_SCAN_INTERVAL] = "invalid_scan_interval"
            else:
                return self.async_create_entry(title="", data=user_input)

        else:
            user_input = {
                CONF_SCAN_INTERVAL: self.config_entry.options.get(
                    CONF_SCAN_INTERVAL, ConfDefaultInt.SCAN_INTERVAL
                ),
            }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=user_input[CONF_SCAN_INTERVAL],
                    ): vol.Coerce(int),
                },
            ),
            errors=errors,
        )

#    async def async_step_adv_pwr_ctl(self, user_input=None) -> FlowResult:
#        """Power Control Options"""
#        errors = {}

#        if user_input is not None:
#            if user_input[ConfName.SLEEP_AFTER_WRITE] < 0:
#                errors[ConfName.SLEEP_AFTER_WRITE] = "invalid_sleep_interval"
#            elif user_input[ConfName.SLEEP_AFTER_WRITE] > 60:
#                errors[ConfName.SLEEP_AFTER_WRITE] = "invalid_sleep_interval"
#            else:
#                return self.async_create_entry(
#                    title="", data={**self.init_info, **user_input}
#                )

 #       else:
 #           user_input = {
 #               ConfName.ADV_STORAGE_CONTROL: self.config_entry.options.get(
 #                   ConfName.ADV_STORAGE_CONTROL,
 #                   bool(ConfDefaultFlag.ADV_STORAGE_CONTROL),
 #               ),
 #               ConfName.ADV_SITE_LIMIT_CONTROL: self.config_entry.options.get(
 #                   ConfName.ADV_SITE_LIMIT_CONTROL,
 #                   bool(ConfDefaultFlag.ADV_SITE_LIMIT_CONTROL),
 #               ),
 #               ConfName.SLEEP_AFTER_WRITE: self.config_entry.options.get(
 #                   ConfName.SLEEP_AFTER_WRITE, ConfDefaultInt.SLEEP_AFTER_WRITE
 #               ),
 #           }

#        return self.async_show_form(
#            step_id="adv_pwr_ctl",
#            data_schema=vol.Schema(
#                {
#                    vol.Required(
#                        f"{ConfName.ADV_STORAGE_CONTROL}",
#                        default=user_input[ConfName.ADV_STORAGE_CONTROL],
#                    ): cv.boolean,
#                    vol.Required(
#                        f"{ConfName.ADV_SITE_LIMIT_CONTROL}",
#                        default=user_input[ConfName.ADV_SITE_LIMIT_CONTROL],
#                    ): cv.boolean,
#                    vol.Optional(
#                        f"{ConfName.SLEEP_AFTER_WRITE}",
#                        default=user_input[ConfName.SLEEP_AFTER_WRITE],
#                    ): vol.Coerce(int),
#                }
#            ),
#            errors=errors,
#        )
