"""Tests for iHomma SmartLight entities."""
import pytest
from unittest.mock import Mock, patch
from homeassistant.const import STATE_ON, STATE_OFF, STATE_UNAVAILABLE
from homeassistant.components.light import ColorMode, ATTR_BRIGHTNESS, ATTR_COLOR_TEMP_KELVIN, ATTR_RGB_COLOR
from custom_components.ihomma_sml.light import iHommaSML_Entity, iHommaSML_GroupEntity
from homeassistant.core import HomeAssistant

@pytest.fixture
def mock_socket(monkeypatch):
    """Mock pour les sockets réseau."""
    class MockSocket:
        def __init__(self, *args, **kwargs):
            pass
            
        def setsockopt(self, *args, **kwargs):
            pass
            
        def settimeout(self, *args, **kwargs):
            pass
            
        def sendto(self, *args, **kwargs):
            return 0
            
        def recvfrom(self, *args, **kwargs):
            return b"HLK_TEST", ("192.168.1.100", 988)
            
        def close(self):
            pass
    
    monkeypatch.setattr("socket.socket", MockSocket)
    return MockSocket()

@pytest.fixture
def light_entity(hass):
    """Fixture pour créer une entité de test"""
    return iHommaSML_Entity(hass, {"name": "Test Light", "device_ip": "192.168.1.100"})

@pytest.mark.asyncio
async def test_light_entity_initialization(hass, mock_socket):
    """Test light entity initialization."""
    entry_infos = {
        "name": "Test Light",
        "device_ip": "192.168.1.100"
    }
    entity = iHommaSML_Entity(hass, entry_infos)
    
    # Vérification de l'unique_id généré
    expected_unique_id = f"ihomma_sml_{entry_infos['device_ip'].replace('.', '_')}"
    assert entity.unique_id == expected_unique_id
    assert entity.name == entry_infos["name"]
    assert not entity.available

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
async def test_light_state_restoration(hass, mock_socket_module):
    """Test light state restoration."""
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
    
    # Déclencher la restauration d'état
    await entity.async_get_light_states()
    
    # Vérifier que l'état a été restauré
    assert entity.state == STATE_ON
    assert entity.brightness == 128
    assert entity.color_temp_kelvin == 4000
    assert entity.rgb_color == (255, 255, 255)

@pytest.mark.asyncio
async def test_light_turn_on(hass, mock_socket_module):
    """Test light turn on."""
    entry_infos = {
        "name": "Test Light",
        "device_ip": "192.168.1.100"
    }
    entity = iHommaSML_Entity(hass, entry_infos)
    
    # Simulation de la disponibilité
    entity._attr_available = True
    
    # Test de l'allumage
    await entity.async_turn_on()
    assert entity.state == STATE_ON
    
    # Test avec luminosité
    await entity.async_turn_on(brightness=128)
    assert entity.brightness == 128
    
    # Test avec température de couleur
    await entity.async_turn_on(color_temp_kelvin=4000)
    assert entity.color_temp_kelvin == 4000
    
    # Test avec couleur RGB
    await entity.async_turn_on(rgb_color=(255, 0, 0))
    assert entity.rgb_color == (255, 0, 0)

@pytest.mark.asyncio
async def test_light_turn_off(hass, mock_socket_module):
    """Test light turn off."""
    entry_infos = {
        "name": "Test Light",
        "device_ip": "192.168.1.100"
    }
    entity = iHommaSML_Entity(hass, entry_infos)
    
    # Simulation de la disponibilité
    entity._attr_available = True
    
    # Test de l'extinction
    await entity.async_turn_off()
    assert entity.state == STATE_OFF

@pytest.mark.asyncio
async def test_effect_translations(hass, mock_socket_module):
    """Test effect translations management."""
    # Configure mock Home Assistant
    hass.config = Mock()
    hass.config.language = "en"
    
    # Mock translations
    translations = {
        "component.ihomma_sml.entity.light.effect.state.strong_white": "Strong white",
        "component.ihomma_sml.entity.light.effect.state.candlelight": "Candle light",
        "component.ihomma_sml.entity.light.effect.state.morning_light": "Morning light",
        "component.ihomma_sml.entity.light.effect.state.nature_light": "Nature light"
    }
    
    with patch('homeassistant.helpers.translation.async_get_translations') as mock_trans:
        mock_trans.return_value = translations
        
        entity = iHommaSML_Entity(hass, {
            "name": "Test Light", 
            "device_ip": "192.168.1.100"
        })
        
        await entity.async_added_to_hass()
        
        # Verify translations
        assert "Strong white" in entity.effect_list
        assert "Candle light" in entity.effect_list
        assert "Morning light" in entity.effect_list
        assert "Nature light" in entity.effect_list
        
        # Verify fallback for untranslated effects
        assert len(entity.effect_list) > len(translations)