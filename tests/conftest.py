"""Common fixtures for iHomma SmartLight tests."""
import pytest
import socket
import asyncio
from pathlib import Path
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from unittest.mock import patch, MagicMock

@pytest.fixture
async def hass(tmp_path) -> HomeAssistant:
    """Fixture pour créer une instance de HomeAssistant pour les tests."""
    hass = HomeAssistant(str(tmp_path))
    await hass.async_start()
    return hass

@pytest.fixture(autouse=True)
def mock_socket_module(monkeypatch):
    """Mock global socket module."""
    mock_socket = MagicMock(spec=socket.socket)
    mock_socket.recvfrom.return_value = (b"HLK_TEST", ("192.168.1.100", 988))
    mock_socket.sendto.return_value = 0

    class MockSocketClass:
        def __init__(self, *args, **kwargs):
            pass
        def __call__(self, *args, **kwargs):
            return mock_socket
        def socket(self, *args, **kwargs):
            return mock_socket

    mock_socket_module = MockSocketClass()
    monkeypatch.setattr(socket, 'socket', mock_socket_module)
    return mock_socket

@pytest.fixture
def mock_light_entity():
    """Fixture to mock light entity configuration."""
    return {
        "name": "Test Light",
        "device_ip": "192.168.1.100"
    }

@pytest.fixture(autouse=True)
def allow_socket(request):
    """Fixture pour autoriser les sockets dans les tests."""
    yield