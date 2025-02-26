"""Tests for iHomma SmartLight device."""
import pytest
from unittest.mock import Mock, patch
from custom_components.ihomma_sml.device import iHommaSML_Device

def test_device_initialization():
    """Test device initialization."""
    device = iHommaSML_Device("192.168.1.100")
    assert device.device_ip == "192.168.1.100"
    assert not device.available
    assert not device.is_on

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