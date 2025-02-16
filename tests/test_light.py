"""Tests for iHomma SmartLight light platform."""
from unittest.mock import patch, MagicMock
import pytest

from homeassistant.const import (
    STATE_ON,
    STATE_OFF,
    STATE_UNAVAILABLE,
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_RGB_COLOR,
)
from homeassistant.components.light import ColorMode
from custom_components.ihomma_sml.light import iHommaSML_Entity

@pytest.fixture
def mock_socket():
    """Mock pour les sockets réseau"""
    with patch('socket.socket') as mock:
        yield mock

@pytest.fixture
def light_entity(hass):
    """Fixture pour créer une entité de test"""
    return iHommaSML_Entity(hass, {"name": "Test Light", "device_ip": "192.168.1.100"})

async def test_light_init(hass, mock_light_entity):
    """Test light initialization."""
    entity = iHommaSML_Entity(hass, mock_light_entity)
    
    assert entity.name == "Test Light"
    assert entity._device_ip == "192.168.1.100"
    assert entity._attr_supported_color_modes == {ColorMode.RGB, ColorMode.COLOR_TEMP}
    assert entity._attr_min_color_temp_kelvin == 2700
    assert entity._attr_max_color_temp_kelvin == 6500

@pytest.mark.asyncio
async def test_light_turn_on(hass, mock_light_entity):
    """Test turning the light on."""
    entity = iHommaSML_Entity(hass, mock_light_entity)
    
    with patch.object(entity, '_iHommaSML_Entity__turnOnOff') as mock_turn_on:
        await entity.async_turn_on()
        mock_turn_on.assert_called_once_with(True)
        assert entity._attr_state == STATE_ON

@pytest.mark.asyncio
async def test_effect_translations(hass):
    """Test la gestion des traductions des effets."""
    with patch('homeassistant.helpers.translation.async_get_translations') as mock_trans:
        mock_trans.return_value = {
            "strong_white": "Strong white/yellow (strong, warm)",
            "candlelight": "Candlelight"
        }
        
        entity = iHommaSML_Entity(hass, {"name": "Test Light", "device_ip": "192.168.1.100"})
        await entity.async_added_to_hass()
        
        assert "Strong white/yellow (strong, warm)" in entity.effect_list
        assert "Candlelight" in entity.effect_list