"""Tests for state manager."""
import pytest
from unittest.mock import Mock
from custom_components.ihomma_sml.state_manager import StateManager

def test_state_manager_singleton():
    """Test state manager singleton pattern."""
    manager1 = StateManager()
    manager2 = StateManager()
    assert manager1 is manager2

def test_state_updates():
    """Test state updates and notifications."""
    manager = StateManager()
    callback = Mock()
    
    manager.register_light("192.168.1.100", callback)
    
    test_state = {
        "state": "on",
        "brightness": 255
    }
    
    manager.update_state("192.168.1.100", test_state)
    callback.assert_called_once_with(test_state)

def test_multiple_subscribers():
    """Test multiple subscribers for same device."""
    manager = StateManager()
    callback1 = Mock()
    callback2 = Mock()
    
    manager.register_light("192.168.1.100", callback1)
    manager.register_light("192.168.1.100", callback2)
    
    test_state = {"state": "on"}
    manager.update_state("192.168.1.100", test_state)
    
    callback1.assert_called_once_with(test_state)
    callback2.assert_called_once_with(test_state)