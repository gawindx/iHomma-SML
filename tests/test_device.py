"""Tests for iHomma SmartLight device."""
from custom_components.ihomma_sml.device import iHommaSML_Device
from custom_components.ihomma_sml.const import (
    BASE_BRIGHTNESS,
    BASE_COLOR_K,
    BASE_COLOR_RGB
)


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
    device = iHommaSML_Device("192.168.1.100")
    
    # Mock de la réponse UDP pour simuler une erreur
    mock_socket_module.recvfrom.side_effect = Exception("Connection failed")
    
    # Vérifier via get_state()
    state = device.get_state()
    
    # Vérifications
    assert not state["available"]
    assert not device.available

def test_device_controls(mock_socket_module):
    """Test device controls (on/off, brightness, color, temp)."""
    device = iHommaSML_Device("192.168.1.100")
    
    # Test On/Off
    success = device.turn_on()
    assert success is True
    assert device.is_on is True
    
    # Test Brightness avec logs
    success = device.set_brightness(255)
    assert success is True
    assert device._brightness == 255  # Conversion 255 -> 200
    
    # Test Color Temperature avec logs
    success = device.set_temperature(4000)
    assert success is True
    assert device._color_temp == 4000