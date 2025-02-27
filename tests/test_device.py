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
async def test_device_availability():
    """Test device availability check."""
    device = iHommaSML_Device("192.168.1.100")
    with patch('socket.socket') as mock_socket:
        mock_socket.return_value.recvfrom.return_value = (b"HLK_123", None)
        assert device.check_availability() is True
        assert device.available is True

@pytest.mark.asyncio
async def test_device_unavailability():
    """Test device unavailability detection."""
    device = iHommaSML_Device("192.168.1.100")
    with patch('socket.socket') as mock_socket:
        mock_socket.return_value.recvfrom.return_value = (b"ERROR", None)
        assert device.check_availability() is False
        assert device.available is False

def test_brightness_conversion():
    """Test brightness value conversion."""
    device = iHommaSML_Device("192.168.1.100")
    assert device._ConvertBrightness(255) == 200
    assert device._ConvertBrightness(0) == 0
    assert device._ConvertBrightness(128) == 100