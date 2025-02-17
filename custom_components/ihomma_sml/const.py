"""Constants for the iHomma SmartLight integration."""

import logging
from typing import Final
from homeassistant.const import Platform

DOMAIN: Final = "ihomma_sml"
PLATFORMS: list[Platform] = [Platform.LIGHT]
UDP_IP = "255.255.255.255"
UDP_PORT = 988
TCP_IP = ""
TCP_PORT = 8080
DEBUG_NETWORK = False
PACKET_SIZES = [752, 1008, 1009, 1010, 1266, 1522, 5677]

_LOGGER = logging.getLogger(__name__)

CONF_DEVICE_IP = "device_ip"
CONF_DEVICES_IP = "devices_ip"
CONF_IS_GROUP = "is_group"

DEFAULT_NAME = "iHomma Light"
DEVICE_MANUFACTURER = "iHomma"
DEVICE_MODEL = "SmartLight"