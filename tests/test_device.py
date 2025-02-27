"""Tests for iHomma SmartLight device."""
import pytest
from unittest.mock import Mock, patch
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
    
    # Simuler une communication réussie
    result = device.__sendUDPPacket(("192.168.1.100", 988), b"test")
    
    # Vérifications
    assert result is not None
    assert device.available is True

def test_device_unavailability(mock_socket_module):
    """Test device unavailability detection."""
    device = iHommaSML_Device("192.168.1.100")
    
    # Modifier le mock pour simuler une erreur
    mock_socket_module.recvfrom.side_effect = Exception("Connection failed")
    
    # Simuler une communication échouée
    result = device.__sendUDPPacket(("192.168.1.100", 988), b"test")
    
    # Vérifications
    assert result is None
    assert device.available is False

def test_brightness_adjustment(mock_socket_module):
    """Test brightness value adjustment."""
    device = iHommaSML_Device("192.168.1.100")
    
    # Test des différentes valeurs de luminosité
    device.set_brightness(255)
    assert device._brightness == 200  # Conversion 255 -> 200
    
    device.set_brightness(128)
    assert device._brightness == 100  # Conversion 128 -> 100
    
    device.set_brightness(0)
    assert device._brightness == 0    # Pas de conversion pour 0

def test_device_send_command(mock_socket_module):
    """Test device command sending."""
    device = iHommaSML_Device("192.168.1.100")
    assert device.turn_on() is True
    assert device.is_on is True

def test_device_brightness(mock_socket_module):
    """Test device brightness control."""
    device = iHommaSML_Device("192.168.1.100")
    assert device.set_brightness(255) is True
    assert device._brightness == 255

def test_device_color_temp(mock_socket_module):
    """Test device color temperature control."""
    device = iHommaSML_Device("192.168.1.100")
    assert device.set_temperature(4000) is True
    assert device._color_temp == 4000

def test_device_rgb_color(mock_socket_module):
    """Test device RGB color control."""
    device = iHommaSML_Device("192.168.1.100")
    assert device.set_color((255, 0, 0)) is True
    assert device._rgb_color == (255, 0, 0)

@pytest.mark.asyncio
async def test_device_availability(mock_socket_module):
    """Test device availability detection."""
    device = iHommaSML_Device("192.168.1.100")
    # Force une réponse valide du mock socket
    mock_socket_module.recvfrom.return_value = (b"HLK_TEST", None)
    
    # Test via la propriété available
    assert device.available is True

@pytest.mark.asyncio
async def test_device_unavailability(mock_socket_module):
    """Test device unavailability detection."""
    device = iHommaSML_Device("192.168.1.100")
    # Force une réponse invalide du mock socket
    mock_socket_module.recvfrom.return_value = (b"ERROR", None)
    
    # Test via la propriété available
    assert device.available is False

def test_brightness_conversion():
    """Test brightness value conversion."""
    device = iHommaSML_Device("192.168.1.100")
    assert device.__ConvertBrightness(255) == 200
    assert device.__ConvertBrightness(0) == 0
    assert device.__ConvertBrightness(128) == 100

def test_device_turn_on(mock_socket_module):
    """Test device turn on command."""
    device = iHommaSML_Device("192.168.1.100")
    
    # Forcer une réponse positive du mock
    mock_socket_module.recvfrom.return_value = (b"HLK_TEST", ("192.168.1.100", 988))
    
    # Test de l'allumage
    success = device.turn_on()
    
    # Vérifications
    assert success is True
    assert device.is_on is True