"""Common fixtures for iHomma SmartLight tests."""
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from unittest.mock import patch

@pytest.fixture
def hass(loop):
    """Fixture to provide a test instance of Home Assistant."""
    hass = HomeAssistant()
    loop.run_until_complete(hass.async_start())
    yield hass
    loop.run_until_complete(hass.async_stop())

@pytest.fixture
def mock_light_entity():
    """Fixture to mock light entity configuration."""
    return {
        "name": "Test Light",
        "device_ip": "192.168.1.100"
    }