"""The iHomma SmartLight integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import DOMAIN, PLATFORMS, _LOGGER

"""Definition of global configuration scheme"""
#CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        # Si vous avez besoin de configuration globale, ajoutez-la ici
    })
}, extra=vol.ALLOW_EXTRA)

async def async_setup(hass: HomeAssistant, config: ConfigEntry) -> bool:
    """Configuration of the iHomma Smartlight integration."""
    if DOMAIN in config:
        _LOGGER.info(
            "Initializing %s integration with plaforms: %s with config: %s",
            DOMAIN,
            PLATFORMS,
            config.get(DOMAIN),
        )
        hass.data[DOMAIN] = config[DOMAIN]
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configuration of an iHomma SmartLight instance from a configenry."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unloading of an iHomma SmartLight instance."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)