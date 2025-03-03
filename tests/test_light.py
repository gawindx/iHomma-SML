"""Tests for iHomma SmartLight entities."""
import pytest
import logging
from unittest.mock import Mock, patch
from homeassistant.const import STATE_ON, STATE_OFF, STATE_UNAVAILABLE
from homeassistant.components.light import ColorMode, ATTR_BRIGHTNESS, ATTR_COLOR_TEMP_KELVIN, ATTR_RGB_COLOR, LightEntityFeature
from custom_components.ihomma_sml.light import iHommaSML_Entity, iHommaSML_GroupEntity
from homeassistant.core import HomeAssistant

# Configuration des logs pour les tests
logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)

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
async def test_light_entity_initialization(hass, mock_socket_module):
    """Test l'initialisation d'une entité light."""
    _LOGGER.debug("=== Démarrage du test d'initialisation de l'entité ===")
    
    # Vérification du fixture hass
    _LOGGER.debug("Vérification de l'instance hass:")
    _LOGGER.debug("- Type: %s", type(hass))
    _LOGGER.debug("- État: %s", hass.state)
    _LOGGER.debug("- Configuration: %s", getattr(hass, 'config', None))
    
    # Préparation des données
    entry_infos = {
        "name": "Test Light",
        "device_ip": "192.168.1.100"
    }
    _LOGGER.debug("Données d'entrée: %s", entry_infos)
    
    # Vérification du mock socket
    _LOGGER.debug("État du mock_socket_module:")
    _LOGGER.debug("- Type: %s", type(mock_socket_module))
    _LOGGER.debug("- Méthodes disponibles: %s", dir(mock_socket_module))
    
    # Création de l'entité avec gestion d'erreur détaillée
    try:
        entity = iHommaSML_Entity(hass, entry_infos)
        _LOGGER.debug("Entité créée avec succès")
    except Exception as e:
        _LOGGER.error("Erreur détaillée lors de la création:")
        _LOGGER.error("- Type d'erreur: %s", type(e))
        _LOGGER.error("- Message: %s", str(e))
        _LOGGER.error("- Arguments: %s", e.args)
        raise

    # Suite des tests avec plus de détails...
    _LOGGER.debug("=== Tests des attributs ===")
    
    expected_unique_id = f"ihomma_sml_{entry_infos['name'].replace(' ', '_').lower()}"
    _LOGGER.debug("Test de l'unique_id:")
    _LOGGER.debug("- Attendu: '%s'", expected_unique_id)
    _LOGGER.debug("- Obtenu: '%s'", entity.unique_id)
    _LOGGER.debug("- Comparaison: %s", str(entity.unique_id) == str(expected_unique_id))
    assert str(entity.unique_id) == str(expected_unique_id)

    # Test des attributs de base
    _LOGGER.debug("Test des attributs - Name: %s, Device IP: %s", entity.name, entity.device_ip)
    assert entity.name == entry_infos["name"]
    assert entity.device_ip == entry_infos["device_ip"]
    
    # Test de disponibilité
    _LOGGER.debug("Test de disponibilité initiale: %s", entity.available)
    assert not entity.available
    
    # Test des modes supportés
    _LOGGER.debug("Test des modes de couleur supportés")
    supported_modes = entity.supported_color_modes
    _LOGGER.debug("Modes supportés: %s", supported_modes)
    assert ColorMode.BRIGHTNESS in supported_modes
    assert ColorMode.COLOR_TEMP in supported_modes
    assert ColorMode.RGB in supported_modes
    
    # Test des fonctionnalités
    _LOGGER.debug("Test des fonctionnalités supportées")
    features = entity.supported_features
    _LOGGER.debug("Fonctionnalités: %s", features)
    assert features & LightEntityFeature.EFFECT
    
    _LOGGER.debug("Test d'initialisation terminé avec succès")

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
    _LOGGER.debug("Démarrage du test d'allumage")
    entry_infos = {"name": "Test Light", "device_ip": "192.168.1.100"}
    entity = iHommaSML_Entity(hass, entry_infos)
    
    _LOGGER.debug("Configuration de la disponibilité")
    entity._attr_available = True
    
    _LOGGER.debug("Test de l'allumage simple")
    await entity.async_turn_on()
    _LOGGER.debug("État après allumage: %s", entity.state)
    assert entity.state == STATE_ON
    
    _LOGGER.debug("Test avec luminosité")
    await entity.async_turn_on(brightness=128)
    _LOGGER.debug("Luminosité après réglage: %s", entity.brightness)
    assert entity.brightness == 128
    
    _LOGGER.debug("Test avec température de couleur")
    await entity.async_turn_on(color_temp_kelvin=4000)
    _LOGGER.debug("Température après réglage: %s", entity.color_temp_kelvin)
    assert entity.color_temp_kelvin == 4000
    
    _LOGGER.debug("Test avec couleur RGB")
    await entity.async_turn_on(rgb_color=(255, 0, 0))
    _LOGGER.debug("Couleur RGB après réglage: %s", entity.rgb_color)
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
    _LOGGER.debug("Démarrage du test des traductions")
    
    _LOGGER.debug("Configuration du mock Home Assistant")
    hass.config = Mock()
    hass.config.language = "en"
    
    translations = {
        "component.ihomma_sml.entity.light.effect.state.strong_white": "Strong white",
        "component.ihomma_sml.entity.light.effect.state.candlelight": "Candle light",
        "component.ihomma_sml.entity.light.effect.state.morning_light": "Morning light",
        "component.ihomma_sml.entity.light.effect.state.nature_light": "Nature light"
    }
    _LOGGER.debug("Traductions configurées: %s", translations)
    
    with patch('homeassistant.helpers.translation.async_get_translations') as mock_trans:
        mock_trans.return_value = translations
        
        _LOGGER.debug("Création de l'entité de test")
        entity = iHommaSML_Entity(hass, {
            "name": "Test Light", 
            "device_ip": "192.168.1.100"
        })
        
        await entity.async_added_to_hass()
        _LOGGER.debug("Liste des effets après initialisation: %s", entity.effect_list)
        
        for effect in ["Strong white", "Candle light", "Morning light", "Nature light"]:
            _LOGGER.debug("Vérification de l'effet: %s", effect)
            assert effect in entity.effect_list
        
        # Verify fallback for untranslated effects
        assert len(entity.effect_list) > len(translations)