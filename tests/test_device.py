"""Tests for iHomma SmartLight device."""
import pytest
import logging
from unittest.mock import Mock, patch
from custom_components.ihomma_sml.device import iHommaSML_Device
from custom_components.ihomma_sml.const import (
    BASE_BRIGHTNESS,
    BASE_COLOR_K,
    BASE_COLOR_RGB
)

# Configuration des logs pour les tests
logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)

def test_device_initialization(mock_socket_module):
    """Test device initialization."""
    device = iHommaSML_Device("192.168.1.100")
    assert device.device_ip == "192.168.1.100"
    assert not device.available

def test_device_availability(mock_socket_module):
    """Test device availability detection."""
    device = iHommaSML_Device("192.168.1.100")
    
    # Vérifier l'état initial
    assert not device.available
    
    # Utiliser get_state() qui va utiliser notre mock
    state = device.get_state()
    
    # Vérifications
    assert state["available"] is True  # Car le mock renvoie "HLK_TEST"
    assert device.available is True    # La propriété doit être mise à jour

def test_device_unavailability(mock_socket_module):
    """Test device unavailability detection."""
    _LOGGER.debug("Démarrage du test d'indisponibilité")
    device = iHommaSML_Device("192.168.1.100")
    
    # Mock de la réponse UDP pour simuler une erreur
    mock_socket_module.recvfrom.side_effect = Exception("Connection failed")
    _LOGGER.debug("Mock configuré pour lever une exception")
    
    # Vérifier via get_state()
    _LOGGER.debug("Appel de get_state()")
    state = device.get_state()
    _LOGGER.debug("État reçu: %s", state)
    
    # Vérifications
    assert not state["available"]
    assert not device.available
    _LOGGER.debug("Test d'indisponibilité terminé avec succès")

def test_device_controls(mock_socket_module):
    """Test device controls (on/off, brightness, color, temp)."""
    device = iHommaSML_Device("192.168.1.100")
    
    # Test On/Off
    assert device.turn_on() is True
    assert device.is_on is True
    assert device.turn_off() is True
    assert device.is_on is not True
    
    # Test Brightness
    assert device.set_brightness(255) is True
    assert device._brightness == 200  # Conversion 255 -> 200
    
    # Test Color Temperature
    assert device.set_temperature(4000) is True
    assert device._color_temp == 4000
    
    # Test RGB Color
    assert device.set_color((255, 0, 0)) is True
    assert device._rgb_color == (255, 0, 0)