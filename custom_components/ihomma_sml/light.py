"""Platform for iHomma SmartLight integration."""

import logging
import socket
from enum import Enum, IntEnum
from time import sleep
from datetime import timedelta
import voluptuous as vol

from .const import (
    DOMAIN, 
    PLATFORMS,
    UDP_IP,
    UDP_PORT,
    TCP_PORT,
    PACKET_SIZES,
    DEBUG_NETWORK,
    _LOGGER,
)

from homeassistant.const import CONF_NAME
from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.translation import async_get_translations
from homeassistant.helpers.restore_state import RestoreEntity

import homeassistant.helpers.config_validation as cv

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_EFFECT,
    ColorMode,
    LightEntity,
    LightEntityFeature,
    PLATFORM_SCHEMA,
)
from .ihomma_effects import AVAILABLE_EFFECTS

"""Definition of configuration keys"""
CONF_DEVICE_IP = "device_ip"

"""Validation scheme for the configuration of the platform"""
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_DEVICE_IP): cv.string,
    }
)

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info = None,  # pylint: disable=unused-argument

):
    """Configuration of the iHomma SmartLight platform from the 
    Configuration found in Configuration.yaml"""

    _LOGGER.debug("Calling iHommaSML async_setup_entry config=%s", config)

    """Configuration validation"""
    try:
        name = config[CONF_NAME]
        device_ip = config[CONF_DEVICE_IP]
    except vol.Invalid as err:
        _LOGGER.error("Configuration invalide : %s", err)
        return False

    """Creation of the entity with validated parameters"""
    entity = iHommaSML_Entity(
        hass,
        {
            "name": name,
            "device_ip": device_ip,
        }
    )
    async_add_entities([entity], True)

class iHommaSML_Entity(LightEntity, RestoreEntity):
    """Representation of an iHommaSML Light."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_infos: dict,
    ) -> None:

        """Initialization of our entity"""
        self._attr_name = entry_infos.get("name")
        self._device_ip = entry_infos.get("device_ip")
        self._udp_address = (self._device_ip, UDP_PORT)
        self._tcp_address = (self._device_ip, TCP_PORT)

        self._hass = hass
        self._attr_has_entity_name = True
        self._translations = {}
        self._attr_online_values = {}

        """Initial Attributes"""
        """The lamp is considered to be unavailable at the start"""
        self._attr_available = False
        self._attr_state = STATE_UNAVAILABLE
        self._was_unavailable = True

        """Kelvin color temperature range and default value"""
        self._attr_min_color_temp_kelvin = 2700  # Hot
        self._attr_max_color_temp_kelvin = 6500  # Cold
        self._attr_color_temp_kelvin = 4000  # Default temperature (neutral)

        """Brightness"""
        self._brightness = 255

        """Initialize the light's default values for RGB mode"""
        self._attr_supported_color_modes = {ColorMode.RGB, ColorMode.COLOR_TEMP}
        self._attr_rgb_color = (255, 255, 255)  # White by default
        self._attr_color_mode = ColorMode.RGB # Default RGB Color mode

        """Initialize the effects"""
        """Effects supported by the bulb"""
        self._attr_supported_features = LightEntityFeature.EFFECT
        self._attr_effect = None  # No start-up effects

        """Create a unique ID based on the IP address of the device"""
        self._attr_unique_id = f"ihomma_sml_{self._attr_name.replace(' ', '_').lower()}"

        """Add the device information"""
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._attr_unique_id)},
            "name": self._attr_name,
            "manufacturer": "iHomma",
            "model": "SmartLight",
            "via_device": (DOMAIN, self._device_ip),
        }

        """Initial save state of the light"""
        self._saved_states = {
            "state": self._attr_state,
            "brightness": self._brightness,
            "effect": self._attr_effect,
            "color_temp_kelvin": self._attr_color_temp_kelvin,
            "rgb_color": self._attr_rgb_color
        }

        """Create a reusable UDP socket"""
        self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._udp_socket.settimeout(0.75)

        _LOGGER.info("Initializing iHommaSML Light entity %s with unique_id %s", 
                    entry_infos.get("name"), 
                    self._attr_unique_id)

        _LOGGER.info("Initializing iHommaSML Light entity %s", entry_infos.get("name"))
        _LOGGER.debug("iHommaSML Light Initialised with:")
        _LOGGER.debug("Name: %s", self._attr_name)
        _LOGGER.debug("Device IP: %s", self._device_ip)

    def update_state(self):
        """Synchronous state update
        Force Home Assistant to be executed async_write_ha_state 
        In the event loop"""
        _LOGGER.debug("Updating state for light %s", self._attr_name)

        self._hass.loop.call_soon_threadsafe(self.async_write_ha_state)

    @property
    def should_poll(self) -> bool:
        """Do not poll for those entities"""

        return False

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend, if any."""

        return "mdi:lightbulb"

    @property
    def name(self) -> str:
        """Return the display name of this light."""

        return self._attr_name

    @property
    def state(self) -> str:
        """Return the state of the light."""

        return self._attr_state

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""

        return self._attr_state == STATE_ON if self._attr_state not in (STATE_UNKNOWN, STATE_UNAVAILABLE) else False

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""

        return self._brightness if self._brightness is not None else 0

    @property
    def color_temp_kelvin(self) -> int | None:
        """Return the CT color value in kelvin."""

        #return self._attr_color_temp_kelvin if self._attr_color_mode == colormode.color_temp sinon aucun
        return self._attr_color_temp_kelvin

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the RGB color value."""

        #return self._attr_rgb_color si self._attr_color_mode == colormode.rgb else nul
        return self._attr_rgb_color

    @property
    def effect(self) -> str | None:
        """Return the current effect of the light."""

        return self._attr_effect

    @property
    def effect_list(self):
        """Return the list of supported effects."""
        _LOGGER.debug("Getting effect list for light %s", self._attr_name)

        return [
            self._translations.get(effect.description_key, effect.id)
            for effect in AVAILABLE_EFFECTS.values()
        ]

    async def async_update(self):
        """Update the state of the entity and manage unavailability."""
        _LOGGER.info("Updating light %s status", self._attr_name)
        _LOGGER.debug("Light %s was Last %s and now is %s",
                   self.name, 
                   ("unavailable" if self._was_unavailable else "available"), 
                   ("available" if self._attr_available else "unavailable"))

        if self._was_unavailable and self._attr_available:
            """The entity becomes available after being unavailable"""
            _LOGGER.debug("Light %s is now available", self.name)
            self.__restore_online_states()
            _LOGGER.info("Light %s is Restoring Last State", self.name)
            _LOGGER.debug("Light %s Restoring Last State with State: %s", self._attr_state)
            _LOGGER.debug("Light %s Restoring Last State with Brigthness: %s", self._brightness)
            _LOGGER.debug("Light %s Restoring Last State with Effect: %s", self._attr_effect)
            _LOGGER.debug("Light %s Restoring Last State with Temp: %s", self._attr_color_temp_kelvin)
            _LOGGER.debug("Light %s Restoring Last State with RGB: %s", self._attr_rgb_color)

            if (self._attr_state == STATE_ON if self._attr_state not in (STATE_UNKNOWN, STATE_UNAVAILABLE) else False):
                _LOGGER.debug("Light %s Restoring ON with last values of brightness/Color/Effect/Warm", self.name)
                kwargs = {}
                if self._brightness is not None:
                    kwargs[ATTR_BRIGHTNESS] = self._brightness
                if self._attr_color_temp_kelvin is not None:
                    kwargs[ATTR_COLOR_TEMP_KELVIN] = self._attr_color_temp_kelvin
                if self._attr_rgb_color is not None:
                    kwargs[ATTR_RGB_COLOR] = self._attr_rgb_color
                if self._attr_effect is not None:
                    kwargs[ATTR_EFFECT] = self._attr_effect
                self.turn_on(**kwargs)
            else:
                _LOGGER.debug("Light %s nedd to be off (state_off/unavailable/unknow", self.name)
                self.turn_off()
        """Store if the entity is unavailable to detect when it comes back online"""
        self._was_unavailable = not self._attr_available

    def turn_on(self, **kwargs) -> None:
        """Instruct the light to turn on."""
        _LOGGER.info("Requets to turn on %s", self._attr_name)
        _LOGGER.debug("Turn on kwargs for %s: %s", self._attr_name, kwargs)

        self._attr_color_mode = ColorMode.RGBW
        if not (self._attr_state in [STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN]):
            result = self.__turnOnOff(True)
            self._attr_state = STATE_ON

        """Light parameters management"""
        if ATTR_BRIGHTNESS in kwargs:
            self._brightness = kwargs[ATTR_BRIGHTNESS]  # Updates the brightness

            self.__SetLuminance(self._brightness)
            _LOGGER.debug("Requets to turn on %s with brightness %s", self._attr_name, self._brightness)

        """Effects management"""
        if ATTR_EFFECT in kwargs:
            effect_str = kwargs[ATTR_EFFECT]  # Home Assistant returns the name translated

            effect = next(
                (effect for effect in AVAILABLE_EFFECTS.values()
                 if self._translations.get(effect.description_key, effect.id) == effect_str),
                None
            )
            """ self._attr_effect = effect_str """
            _LOGGER.debug("Selected Effect: %s of %s", effect_str, self.effect_list)

            if effect is not None:
                _LOGGER.debug("Selected Effect: %s", effect_str)
                self._attr_effect = effect_str
                self._attr_color_mode = ColorMode.RGB

                _LOGGER.debug("Selected Effect Key: %s of %s (%s)", effect_str, effect.id, effect.instruction)
                self.__SetPredefinedLight(effect.instruction)
            else:
                _LOGGER.debug("Effect %s is not valid, disabling effects", effect_str)
        else:
            self._attr_effect = None  # Disabling effects

        """Check if a color temperature is passed"""
        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            temp = kwargs[ATTR_COLOR_TEMP_KELVIN]
            if self._attr_min_color_temp_kelvin <= temp <= self._attr_max_color_temp_kelvin:
                self._attr_color_mode = ColorMode.COLOR_TEMP
                self._attr_color_temp_kelvin = temp
                self.__SetWarmth(self._attr_color_temp_kelvin)

        """Check if an RGB color is passed"""
        if ATTR_RGB_COLOR in kwargs:
            self._attr_rgb_color = kwargs[ATTR_RGB_COLOR]
            _LOGGER.debug("Requets to turn on %s with Color %s with type: %s", self._attr_name, self._attr_rgb_color, type(self._attr_rgb_color))
            self.__SetColor(list(self._attr_rgb_color))

        self.update_state()

    def turn_off(self, **kwargs) -> None:
        """Instruct the light to turn off."""
        _LOGGER.info("Turning off light %s", self._attr_name)

        result = self.__turnOnOff()
        self._attr_state = STATE_OFF
        _LOGGER.debug("Requets result: %s", result)
        self.update_state()

    @callback
    async def async_added_to_hass(self):
        """This callback is called when the entity is added to HA """
        _LOGGER.info("Adding light %s to Home Assistant", self._attr_name)

        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            self._attr_state = last_state.state
            self._brightness = last_state.attributes.get("brightness", 255)
            self._attr_effect = last_state.attributes.get("effect", None)
            self._attr_color_temp_kelvin = last_state.attributes.get("color_temp_kelvin", None)
            self._attr_rgb_color = last_state.attributes.get("rgb_color", None)
        self.__backup_online_states()

        """Arm the timer"""
        timer_cancel = async_track_time_interval(
            self._hass,
            self.async_get_light_states,
            interval = timedelta(seconds=2),
        )
        """Disarm the timer when the entity is destroyed"""
        self.async_on_remove(timer_cancel)

        """Determine Home Assistant's current language"""
        language = self.hass.config.language
        self._translations = await async_get_translations(
            self.hass, 
            language, 
            integrations = [DOMAIN],
            category = "entity"
        )
        _LOGGER.debug("Get translations for light %s", self._translations)

        """Update state after entity loading"""
        self.async_write_ha_state()

    async def async_get_light_states(self, *_):
        """Check the lamp state every 2 seconds and update Home Assistant."""
        _LOGGER.debug("Checking status for light %s", self._attr_name)

        self._attr_available = self.__get_avaibility()
        
        """Determine the correct state based on availability and lamp state"""
        if not self._attr_available:
            self._attr_state = STATE_UNAVAILABLE
            self._was_unavailable = True
        else:
            await self.async_update()
            self.__backup_online_states()

        """Log the lamp state"""
        state_msg = "On" if self._attr_state == STATE_ON else "Off" if self._attr_state == STATE_OFF else "Unavailable"
        _LOGGER.debug("iHommaSML Light (%s, %s) status is: %s", 
                     self._attr_name, self._device_ip, state_msg)

        """Save the updated state"""
        self.async_write_ha_state()

    """Begin of private methods"""

    def __get_avaibility(self) -> bool:
        """Check if the light is available"""
        _LOGGER.debug("Checking availability for light %s", self._attr_name)
        
        watchdog = self.__sendUDPPacket(self._udp_address, "HLK")
        return watchdog is not None

    def __backup_online_states(self):
        """Save the light's online states"""
        _LOGGER.debug("Backing up online states for light %s", self._attr_name)

        self._saved_states.update({
            'state': self._attr_state,
            'brightness': self._brightness,
            'effect': self._attr_effect,
            'color_temp_kelvin': self._attr_color_temp_kelvin,
            'rgb_color': self._attr_rgb_color
        })

    def __restore_online_states(self):
        """Restore the light's online states"""
        _LOGGER.debug("Restoring online states for light %s", self._attr_name)

        self._attr_state = self._saved_states["state"]
        self._brightness = self._saved_states["brightness"]
        self._attr_effect = self._saved_states["effect"]
        self._attr_color_temp_kelvin = self._saved_states["color_temp_kelvin"]
        self._attr_rgb_color = self._saved_states["rgb_color"]

    """ 
        The following methods are based on the work of Jeremiah aka 'lp1dev'
        https://github.com/lp1dev/OpeniHomma-Client/tree/master
    """
    def __parseMessage(self, message):
        """Converts a message to bytes if necessary"""
        _LOGGER.debug("Parsing message: %s", message)

        if type(message) == bytes:
            return message
        else:
            return message.encode()

    def __sendUDPPacket(self, address, message, wait_response=True):
        """Sends a UDP message to the specified address"""
        _LOGGER.debug("Sending UDP packet to %s:%s", address[0], address[1])

        packet = self.__parseMessage(message)
        if DEBUG_NETWORK:
            _LOGGER.debug("UDP target IP: %s", address)
            _LOGGER.debug("UDP target port: %s", UDP_PORT)
            _LOGGER.debug("message string: %s", message)
            _LOGGER.debug("message bytes: %s", packet)

        sent = self._udp_socket.sendto(packet, address)
        if wait_response:
            try:
                return self._udp_socket.recvfrom(2048)
            except Exception as e:
                _LOGGER.debug("Exception in __sendUDPPacket: %s", e)
                return None
        return sent

    def __sendTCPPacket(self, address, message, wait_response=False):
        """Sends a TCP message to the specified address"""
        _LOGGER.debug("Sending TCP packet to %s:%s", address[0], address[1])

        packet = self.__parseMessage(message)
        if DEBUG_NETWORK:
            _LOGGER.debug("TCP target IP: %s", address[0])
            _LOGGER.debug("TCP target Port: %s", address[1])
            try:
                _LOGGER.debug("Message string: %s", packet.decode())
            except Exception as e:
                _LOGGER.debug("Exception in __sendTCPPacket: %s", e)
                pass
            _LOGGER.debug("Message bytes: %s", packet)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        sock.connect(address)
        response = sock.send(packet)
        if wait_response:
            try:
                response = sock.recv(1024)
                return [hex(byte) for byte in response]
            except Exception as e:
                _LOGGER.debug("Exception in __sendTCPPacket: %s", e)
                return None
        _LOGGER.debug("__sendTCPPacket response: %s", response)
        return response

    def __getLampJSONData(self):
        """Get the light's JSON data"""
        _LOGGER.debug("Getting JSON data for light %s", self._attr_name)

        packet = self.__ForgeInstruction(0x2e, 0, [0xff])
        _LOGGER.debug("__getLampJSONData Packet: %s", packet)
        return self.__sendTCPPacket(self._tcp_address, packet)

    def __ForgeInstruction(self, instruction, write_switch, data, final_byte=0):
        """Forge an instruction packet for the light"""
        _LOGGER.debug("Forging instruction: 0x%x with data %s", instruction, data)

        header = [0xfe, 0xef]
        message_length = len(data) + 1 + 1 + 1 + (1 if final_byte else 0)# données + instruction + write_switch + last_byte

        packet = header + [message_length, instruction, write_switch] + data
        packet_size = final_byte
        last_byte = 0
        for byte in packet:
            packet_size += byte
        for size in PACKET_SIZES:
            if size >= packet_size:
                last_byte = size - packet_size + (1 if final_byte else 0)
                _LOGGER.debug("Last byte: %s | Size: %s", last_byte, size)
                if last_byte > 255:
                    continue
                packet.append(last_byte)
                if final_byte:
                    packet.append(final_byte)
                _LOGGER.debug("Last byte: %s | Packet Size: %s", last_byte, packet_size + last_byte)
                _LOGGER.debug("Packet bytes: %s", packet)
                return bytes(packet)
        packet[2] -= 1
        packet.append(final_byte)
        _LOGGER.debug("Final Packet bytes: %s", packet)
        return bytes(packet)

    def __ConvertBrightness(self, value):
        """Convert a value from scale [0, 255] to [0, 200]."""

        """Ensure value is between 0 and 255"""
        value = max(0, min(255, value))

        converted = int(value * (200 / 255))
        _LOGGER.debug("Converting brightness from %s to %s", value, converted)
        return converted

    def __ConvertTempKelvin(self, value):
        """Convert a value from scale [2700, 6500] to [0, 200]."""

        """Ensure value is between 2700 and 6500"""
        value = max(self._attr_min_color_temp_kelvin, 
                    min(self._attr_max_color_temp_kelvin, value))

        converted = (200 - int((value - self._attr_min_color_temp_kelvin) * 200 / (self._attr_max_color_temp_kelvin - self._attr_min_color_temp_kelvin)))
        _LOGGER.debug("Converting temperature from %sK to %s", value, converted)
        return converted
    
    def __turnOnOff(self, on = False):
        """Turn the light on or off"""
        _LOGGER.info("Turning light %s %s", self._attr_name, "on" if on else "off")
        _LOGGER.debug("Execute turnOnOff: %s", "TurnOn" if on else "TurnOff")

        value = 17 if on else 18
        packet = self.__ForgeInstruction(0xa3, 1, [value])
        result = self.__sendTCPPacket(self._tcp_address, packet)
        _LOGGER.debug("TurnOnOff result: %s", result)
        return result

    def __SetLuminance(self, value):
        """Set the light's brightness"""
        _LOGGER.info("Setting brightness to %s for light %s", value, self._attr_name)
        _LOGGER.debug("setBrightness : %s", value)

        converted = self.__ConvertBrightness(value)
        packet = self.__ForgeInstruction(0xa7, 1, [converted])
        result = self.__sendTCPPacket(self._tcp_address, packet)
        _LOGGER.debug("SetLuminance result: %s", result)
        return result

    def __SetWarmth(self, value):
        """Set the light's color temperature"""
        _LOGGER.info("Setting color temperature to %sK for light %s", value, self._attr_name)
        _LOGGER.debug("setWarmth : %s°K", value)

        converted = self.__ConvertTempKelvin(value)
        packet = self.__ForgeInstruction(0xa1, 1, [converted], 94)
        result = self.__sendTCPPacket(self._tcp_address, packet)
        _LOGGER.debug("SetWarmth result: %s", result)
        return result

    def __SetColor(self, value):
        """Set the light's RGB color"""
        _LOGGER.info("Setting RGB color to %s for light %s", value, self._attr_name)
        _LOGGER.debug("setColor : %s", value)

        final_byte = 0
        if (value == [255, 0, 0]) or (value == [0, 255, 0]) or (value == [0, 0, 255]):
            final_byte = 94
            _LOGGER.debug("Using final byte 94 for primary color")
        packet = self.__ForgeInstruction(0xa1, 1, value, final_byte)
        result = self.__sendTCPPacket(self._tcp_address, packet)
        _LOGGER.debug("SetColor result: %s", result)
        return result

    def __SetPredefinedLight(self, effect):
        """Set the light's effect"""
        _LOGGER.info("Setting effect %s for light %s", effect, self._attr_name)
        _LOGGER.debug("Set Effect Light: %s ", effect)

        packet = self.__ForgeInstruction(0xa5, 1, [effect])
        result = self.__sendTCPPacket(self._tcp_address, packet)
        _LOGGER.debug("SetPredefinedLight result: %s", result)
        return result
