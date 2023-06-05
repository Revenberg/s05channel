"""Constants for the Detailed Hello World Push integration."""

from enum import IntEnum

DOMAIN = "s05channel"
DEFAULT_NAME = "S0Channel"


CONF_PATH = "s0Path"

CONF_MANUAL_PATH = "Enter Manually"

CONF_SCAN_INTERVAL = 60


HOST = "/dev/ttyACM0"
    
class RetrySettings(IntEnum):
    """Retry settings when opening a connection to the inverter fails."""

    Time = 800  # first attempt in milliseconds
    Ratio = 2  # time multiplier between each attempt
    Limit = 4  # number of attempts before failing

class ConfDefaultInt(IntEnum):
    """ConfDefaultInt."""
    
    SCAN_INTERVAL = 60

# parameter names per sunspec
DEVICE_STATUS = {
    1: "I_STATUS_OFF",
    2: "I_STATUS_SLEEPING",
    3: "I_STATUS_STARTING",
    4: "I_STATUS_MPPT",
    5: "I_STATUS_THROTTLED",
    6: "I_STATUS_SHUTTING_DOWN",
    7: "I_STATUS_FAULT",
    8: "I_STATUS_STANDBY",
}

# English descriptions of parameter names
DEVICE_STATUS_TEXT = {
    1: "Off",
    2: "Sleeping (Auto-Shutdown)",
    3: "Grid Monitoring",
    4: "Production",
    5: "Production (Curtailed)",
    6: "Shutting Down",
    7: "Fault",
    8: "Maintenance",
    9: "Running",
}
