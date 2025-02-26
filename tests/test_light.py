"""Tests for iHomma SmartLight entities."""
import pytest
from unittest.mock import Mock, patch
from homeassistant.const import STATE_ON, STATE_OFF, STATE_UNAVAILABLE, ATTR_BRIGHTNESS, ATTR_COLOR_TEMP_KELVIN, ATTR_RGB_COLOR
from homeassistant.components.light import ColorMode
from custom_components.ihomma_sml.light import iHommaSML_Entity, iHommaSML_GroupEntity

@pytest.fixture
def mock_socket():
    """Mock pour les sockets réseau"""
    with patch('socket.socket') as mock:
        yield mock

@pytest.fixture
def light_entity(hass):
    """Fixture pour créer une entité de test"""
    return iHommaSML_Entity(hass, {"name": "Test Light", "device_ip": "192.168.1.100"})

@pytest.mark.asyncio
async def test_light_entity_initialization():
    """Test light entity initialization."""
    hass = Mock()
    entry_infos = {
        "name": "Test Light",
        "device_ip": "192.168.1.100"
    }
    entity = iHommaSML_Entity(hass, entry_infos)
    assert entity.name == "Test Light"
    assert entity.unique_id == "ihomma_sml_192_168_1_100"
    assert entity.available is False

@pytest.mark.asyncio
async def test_group_entity_initialization():
    """Test group entity initialization."""
    hass = Mock()
    entry_infos = {
        "name": "Test Group",
        "devices_ip": ["192.168.1.100", "192.168.1.101"]
    }
    entity = iHommaSML_GroupEntity(hass, entry_infos)
    assert entity.name == "Test Group"
    assert len(entity._devices) == 2
    assert entity.available is False

@pytest.mark.asyncio
async def test_light_state_restoration():
    """Test light state restoration."""
    hass = Mock()
    entry_infos = {
        "name": "Test Light",
        "device_ip": "192.168.1.100"
    }
    entity = iHommaSML_Entity(hass, entry_infos)
    
    # Simuler un état sauvegardé
    entity._saved_states = {
        "state": STATE_ON,
        "brightness": 128,
        "effect": None,
        "color_temp_kelvin": 4000,
        "rgb_color": (255, 255, 255)
    }
    
    entity._attr_available = True
    entity._was_unavailable = True
    await entity.async_update()
    
    assert entity.state == STATE_ON
    assert entity.brightness == 128

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