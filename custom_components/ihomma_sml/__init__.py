"""The iHomma SmartLight integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import (
    DOMAIN,
    PLATFORMS,
    CONF_DEVICES_IP,
    CONF_IS_GROUP,
)

_LOGGER = logging.getLogger(__name__)

"""Definition of global configuration scheme"""
CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_IS_GROUP, default=False): cv.boolean,
        vol.Optional(CONF_DEVICES_IP): vol.All(
            cv.ensure_list,
            [cv.string],
            vol.Length(min=1, msg="Au moins une IP est requise pour un groupe")
        ),
    })
}, extra=vol.ALLOW_EXTRA)

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Setup de l'intégration iHomma SmartLight."""
    if DOMAIN in config:
        conf = config.get(DOMAIN, {})
        _LOGGER.info(
            "Initializing %s integration with config: %s",
            DOMAIN,
            conf
        )
        hass.data[DOMAIN] = conf
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configuration of an iHomma SmartLight instance from a configenry."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unloading of an iHomma SmartLight instance."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)