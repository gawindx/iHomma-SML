"""Common fixtures for iHomma SmartLight tests."""
import pytest
import socket
import asyncio
from pathlib import Path
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from unittest.mock import patch, MagicMock, Mock

@pytest.fixture
async def hass(tmp_path) -> HomeAssistant:
    """Fixture pour créer une instance de HomeAssistant pour les tests."""
    hass = HomeAssistant(str(tmp_path))
    await hass.async_start()
    return hass

@pytest.fixture(autouse=True)
def mock_socket_module(monkeypatch):
    """Mock global socket module."""
    class MockSocket:
        def __init__(self, *args, **kwargs):
            pass
            
        def setsockopt(self, *args, **kwargs):
            return None
            
        def settimeout(self, *args, **kwargs):
            return None
            
        def sendto(self, data, addr):
            return len(data)
            
        def recvfrom(self, bufsize):
            return b"HLK_TEST", ("192.168.1.100", 988)
            
        def close(self):
            pass
            
        def fileno(self):
            """Méthode requise pour les tests asyncio."""
            return 0

    # Remplacement du socket par notre mock
    monkeypatch.setattr("socket.socket", lambda *args, **kwargs: MockSocket())
    
    mock_socket = MockSocket()
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