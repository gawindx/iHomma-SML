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
    # Nouvelle façon de tester avec plus de détails
    actual_id = str(entity.unique_id).strip()
    expected_id = str(expected_unique_id).strip()
    
    assert actual_id == expected_id
    _LOGGER.debug("Test de l'unique_id réussi")
    
    # Test des attributs de base
    _LOGGER.debug("Test des attributs - Name: %s", entity._attr_name)
    assert entity._attr_name == entry_infos["name"]
    
    # Test de disponibilité
    _LOGGER.debug("Test de disponibilité initiale: %s", entity._attr_available)
    assert not entity._attr_available
    
    # Test des modes supportés
    _LOGGER.debug("Test des modes de couleur supportés")
    supported_modes = entity._attr_supported_color_modes
    _LOGGER.debug("Modes supportés: %s", supported_modes)
    assert ColorMode.COLOR_TEMP in supported_modes
    assert ColorMode.RGB in supported_modes
    
    # Test des fonctionnalités
    _LOGGER.debug("Test des fonctionnalités supportées")
    features = entity._attr_supported_features
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
    _LOGGER.debug("=== Démarrage du test de restauration d'état ===")
    
    # Configuration initiale
    entry_infos = {
        "name": "Test Light",
        "device_ip": "192.168.1.100"
    }
    
    # Mock de l'état précédent
    mock_restored_state = Mock()
    mock_restored_state.state = STATE_ON
    mock_restored_state.attributes = {
        "brightness": 128,
        "color_temp_kelvin": 4000,
        "rgb_color": (255, 255, 255),
        "effect": None,
        "supported_color_modes": [ColorMode.BRIGHTNESS, ColorMode.COLOR_TEMP, ColorMode.RGB],
        "supported_features": LightEntityFeature.EFFECT
    }
    
    # Configuration des mocks et hass
    async def mock_async_get_last_state():
        _LOGGER.debug("Mock async_get_last_state appelé")
        return mock_restored_state
    
    async def mock_async_get_translations(*args, **kwargs):
        _LOGGER.debug("Mock async_get_translations appelé avec: %s, %s", args, kwargs)
        return {
            "component.ihomma_sml.entity.light.effect.state.strong_white": "Strong white",
            "component.ihomma_sml.entity.light.effect.state.candlelight": "Candle light"
        }
    
    # Configuration de hass
    hass.config = Mock()
    hass.config.language = "en"
    
    with patch('homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state', 
              new=mock_async_get_last_state), \
         patch('homeassistant.helpers.translation.async_get_translations',
              side_effect=mock_async_get_translations):
        
        _LOGGER.debug("Création de l'entité")
        entity = iHommaSML_Entity(hass, entry_infos)
        entity.hass = hass
        
        _LOGGER.debug("Déclenchement de async_added_to_hass")
        await entity.async_added_to_hass()
        
        _LOGGER.debug("=== Vérification des états ===")
        _LOGGER.debug("État actuel: %s", entity.state)
        _LOGGER.debug("Luminosité: %s", getattr(entity, 'brightness', None))
        _LOGGER.debug("Température: %s", getattr(entity, 'color_temp_kelvin', None))
        
        # Vérifications
        assert entity.state == STATE_ON
        assert entity.brightness == 128
        assert entity.color_temp_kelvin == 4000
        
        _LOGGER.debug("Test de restauration terminé avec succès")

@pytest.mark.asyncio
async def test_light_turn_on(hass, mock_socket_module):
    """Test light turn on."""
    _LOGGER.debug("Démarrage du test d'allumage")
    
    # Configuration de l'entité
    entry_infos = {"name": "Test Light", "device_ip": "192.168.1.100"}
    
    # Création et configuration de l'entité
    entity = iHommaSML_Entity(hass, entry_infos)
    entity.hass = hass  # S'assurer que hass est défini
    await entity.async_added_to_hass()  # Important pour initialiser l'entité
    
    _LOGGER.debug("Configuration de la disponibilité")
    entity._attr_available = True
    
    # Test de l'allumage
    _LOGGER.debug("Test de l'allumage simple")
    await entity.async_turn_on()
    _LOGGER.debug("État après allumage: %s", entity.state)
    
    # Vérification de l'état
    state = entity.state
    _LOGGER.debug("État final: %s", state)
    assert state == STATE_ON
    
    # Tests des attributs
    _LOGGER.debug("Test avec luminosité")
    await entity.async_turn_on(brightness=128)
    _LOGGER.debug("Luminosité après réglage: %s", entity.brightness)
    assert entity.brightness == 128

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