"""Constants for the iHomma SmartLight integration."""

from typing import Final
from homeassistant.const import Platform

DOMAIN: Final = "ihomma_sml"
PLATFORMS: list[Platform] = [Platform.LIGHT]

# Configuration keys
CONF_DEVICE_IP = "device_ip"
CONF_DEVICES_IP = "devices_ip"
CONF_IS_GROUP = "is_group"

# Network constants
DEBUG_NETWORK = False
PACKET_SIZES = [752, 1008, 1009, 1010, 1266, 1522, 5677]
TCP_PORT = 8080
UDP_IP = "255.255.255.255"
UDP_PORT = 988
UDP_TIMEOUT = 1

# Default Values for the integration
BASE_BRIGHTNESS = 255
BASE_COLOR_K = 4000
BASE_COLOR_RGB = (255, 255, 255)
TEMP_COLOR_MAX_K = 6500
TEMP_COLOR_MIN_K = 2700

